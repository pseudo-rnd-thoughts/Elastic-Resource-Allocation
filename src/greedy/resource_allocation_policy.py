"""Bid policy functions"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

from docplex.cp.model import CpoModel, SOLVE_STATUS_OPTIMAL

from src.core.server import Server
from src.core.task import Task


class ResourceAllocationPolicy(ABC):
    """Resource Allocation Policy class that is inherited with each option"""

    def __init__(self, name):
        self.name = name

    def allocate(self, task: Task, server: Server) -> Tuple[int, int, int]:
        """
        Determines the resource speed for the task on the server but finding the smallest
        :param task: The task
        :param server: The server
        :return: A tuple of resource speeds
        """

        """
        Old code however very inefficient for large available bandwidth
        return min(((s, w, r)
                    for s in range(1, server.available_bandwidth + 1)
                    for w in range(1, server.available_computation + 1)
                    for r in range(1, server.available_bandwidth - s + 1)
                    if task.required_storage * w * r + s * task.required_computation * r +
                    s * w * task.required_results_data <= task.deadline * s * w * r),
                    key=lambda bid: self.evaluator(task, server, bid[0], bid[1], bid[2]))
                    
        min_value = inf
        min_speeds = None

        for s in range(1, server.available_bandwidth + 1):
            for w in range(1, server.available_computation + 1):
                for r in range(1, server.available_bandwidth - s + 1):
                    if task.required_storage * w * r + s * task.required_computation * r + 
                    s * w * task.required_results_data <= task.deadline * s * w * r:
                        value = self.evaluate(task, server, s, w, r)
                        if value < min_value:
                            min_value = value
                            min_speeds = (s, w, r)
                        break
        return min_speeds
        """

        assert server.available_computation >= 1
        assert server.available_bandwidth >= 2

        model = CpoModel("Resource Allocation")

        loading_speed = model.integer_var(min=1, max=server.available_bandwidth, name="loading speed")
        compute_speed = model.integer_var(min=1, max=server.available_computation, name="compute speed")
        sending_speed = model.integer_var(min=1, max=server.available_bandwidth, name="sending speed")

        model.add(task.required_storage / loading_speed + task.required_computation / compute_speed +
                  task.required_results_data / sending_speed <= task.deadline)
        model.add(loading_speed + sending_speed <= server.available_bandwidth)

        model.minimize(self.evaluate(task, server, loading_speed, compute_speed, sending_speed))

        model_solution = model.solve(log_output=None)

        if model_solution.get_solve_status() != SOLVE_STATUS_OPTIMAL:
            print("Error in resource allocation as model solution is {}".format(model_solution.get_search_status()))
            print("Available storage: {}, computation: {}, bandwidth: {}"
                  .format(server.available_storage, server.available_computation, server.available_bandwidth))
            print("Required storage: {}, compute: {}, results data: {}"
                  .format(task.required_storage, task.required_computation, task.required_results_data))
        else:
            return model_solution.get_value(loading_speed), \
                   model_solution.get_value(compute_speed), \
                   model_solution.get_value(sending_speed)

    @abstractmethod
    def evaluate(self, task: Task, server: Server,
                 loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """
        A resource evaluator that measures how good a choice of loading, compute and sending speed
        :param task: A task
        :param server: A server
        :param loading_speed: The loading speed of the storage
        :param compute_speed: The compute speed of the required computation
        :param sending_speed: The sending speed of the results data
        :return: A float of the resource speed
        """
        pass


class SumPercentage(ResourceAllocationPolicy):
    """The sum of percentage"""

    def __init__(self):
        super().__init__("Percentage Sum")

    def evaluate(self, task: Task, server: Server, loading_speed: int, compute_speed: int,
                 sending_speed: int) -> float:
        """Resource evaluator"""
        return compute_speed / server.available_computation + \
               (loading_speed + sending_speed) / server.available_bandwidth


class SumSpeed(ResourceAllocationPolicy):
    """The sum of resource speeds"""

    def __init__(self):
        super().__init__("Sum of speeds")

    def evaluate(self, task: Task, server: Server,
                 loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """Resource evaluator"""
        return loading_speed + compute_speed + sending_speed


class DeadlinePercent(ResourceAllocationPolicy):
    """Ratio of speeds divided by deadline"""

    def __init__(self):
        super().__init__("Deadline Percent")

    def evaluate(self, task: Task, server: Server, loading_speed: int, compute_speed: int,
                 sending_speed: int) -> float:
        """Resource evaluator"""
        return (task.required_storage / loading_speed +
                task.required_computation / compute_speed +
                task.required_results_data / sending_speed) / task.deadline


policies = (
    SumPercentage(),
    SumSpeed()
)

max_name_length = max(len(policy.name) for policy in policies)
