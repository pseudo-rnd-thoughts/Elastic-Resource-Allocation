"""Bid policy functions"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

from docplex.cp.model import CpoModel

from core.job import Job
from core.server import Server
from math import inf

class ResourceAllocationPolicy(ABC):
    """Resource Allocation Policy class that is inherited with each option"""

    def __init__(self, name):
        self.name = name

    def allocate(self, job: Job, server: Server) -> Tuple[int, int, int]:
        """
        Determines the resource speed for the job on the server but finding the smallest
        :param job: The job
        :param server: The server
        :return: A tuple of resource speeds
        """

        """
        Old code however very inefficient for large available bandwidth
        return min(((s, w, r)
                    for s in range(1, server.available_bandwidth + 1)
                    for w in range(1, server.available_computation + 1)
                    for r in range(1, server.available_bandwidth - s + 1)
                    if job.required_storage * w * r + s * job.required_computation * r +
                    s * w * job.required_results_data <= job.deadline * s * w * r),
                    key=lambda bid: self.evaluator(job, server, bid[0], bid[1], bid[2]))
                    
        min_value = inf
        min_speeds = None

        for s in range(1, server.available_bandwidth + 1):
            for w in range(1, server.available_computation + 1):
                for r in range(1, server.available_bandwidth - s + 1):
                    if job.required_storage * w * r + s * job.required_computation * r + s * w * job.required_results_data <= job.deadline * s * w * r:
                        value = self.evaluate(job, server, s, w, r)
                        if value < min_value:
                            min_value = value
                            min_speeds = (s, w, r)
                        break
        return min_speeds
        """

        model = CpoModel("Resource Allocation")

        loading_speed = model.integer_var(min=1, max=server.available_bandwidth - 1, name="loading speed")
        compute_speed = model.integer_var(min=1, max=server.available_computation, name="compute speed")
        sending_speed = model.integer_var(min=1, max=server.available_bandwidth - 1, name="sending speed")

        model.add(job.required_storage / loading_speed + job.required_computation / compute_speed +
                  job.required_results_data / sending_speed <= job.deadline)
        model.add(loading_speed + sending_speed <= server.available_bandwidth)

        model.minimize(self.evaluate(job, server, loading_speed, compute_speed, sending_speed))

        model_solution = model.solve(log_output=None)

        return model_solution.get_value(loading_speed), \
            model_solution.get_value(compute_speed), \
            model_solution.get_value(sending_speed)

    @abstractmethod
    def evaluate(self, job: Job, server: Server,
                 loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """
        A resource evaluator that measures how good a choice of loading, compute and sending speed
        :param job: A job
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

    def evaluate(self, job: Job, server: Server, loading_speed: int, compute_speed: int,
                 sending_speed: int) -> float:
        """Resource evaluator"""
        return compute_speed / server.available_computation + \
            (loading_speed + sending_speed) / server.available_bandwidth


class SumSpeed(ResourceAllocationPolicy):
    """The sum of resource speeds"""

    def __init__(self):
        super().__init__("Sum of speeds")

    def evaluate(self, job: Job, server: Server,
                 loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """Resource evaluator"""
        return loading_speed + compute_speed + sending_speed


class DeadlinePercent(ResourceAllocationPolicy):
    """Ratio of speeds divided by deadline"""

    def __init__(self):
        super().__init__("Deadline Percent")

    def evaluate(self, job: Job, server: Server, loading_speed: int, compute_speed: int,
                 sending_speed: int) -> float:
        """Resource evaluator"""
        return (job.required_storage / loading_speed +
                job.required_computation / compute_speed +
                job.required_results_data / sending_speed) / job.deadline


policies = (
    SumPercentage(),
    SumSpeed()
)

max_name_length = max(len(policy.name) for policy in policies)
