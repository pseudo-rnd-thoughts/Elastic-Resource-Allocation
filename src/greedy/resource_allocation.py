"""Bid policy functions"""

from __future__ import annotations

from abc import ABC, abstractmethod
from random import gauss
from typing import TYPE_CHECKING, Optional

from docplex.cp.model import CpoModel, SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL

if TYPE_CHECKING:
    from typing import Tuple

    from src.core.elastic_task import ElasticTask
    from src.core.server import Server


class ResourceAllocation(ABC):
    """Resource Allocation class that is inherited with each option"""

    def __init__(self, name):
        self.name = name

    def allocate(self, task: ElasticTask, server: Server) -> Tuple[int, int, int]:
        """
        Determines the resource speed for the task on the server but finding the smallest

        :param task: The task
        :param server: The server
        :return: A tuple of resource speeds
        """

        """
        Initial version that attempts brute force however too computationally expensive when the discretisation of the 
            server resources is too high
        return min(((s, w, r)
                    for s in range(1, server.available_bandwidth + 1)
                    for w in range(1, server.available_computation + 1)
                    for r in range(1, server.available_bandwidth - s + 1)
                    if task.required_storage * w * r + s * task.required_computation * r +
                    s * w * task.required_results_data <= task.deadline * s * w * r),
                   key=lambda bid: self.resource_evaluator(task, server, bid[0], bid[1], bid[2]))"""
        # TODO possible to use KKT
        model = CpoModel('resource allocation')

        loading = model.integer_var(min=1, max=server.available_bandwidth - 1)
        compute = model.integer_var(min=1, max=server.available_computation)
        sending = model.integer_var(min=1, max=server.available_bandwidth - 1)

        model.add(task.required_storage * compute * sending +
                  loading * task.required_computation * sending +
                  loading * compute * task.required_results_data <=
                  task.deadline * loading * compute * sending)
        model.add(loading + sending <= server.available_bandwidth)

        model.minimize(self.resource_evaluator(task, server, loading, compute, sending))
        model_solution = model.solve(log_output=None)

        if model_solution.get_solve_status() != SOLVE_STATUS_FEASIBLE and \
                model_solution.get_solve_status() != SOLVE_STATUS_OPTIMAL:
            print(f'Resource allocation fail - status: {model_solution.get_solve_status()} '
                  f'for {str(task)} and {str(server)}')
            raise Exception(f'Resource allocation for a task is infeasible, '
                            f'model solution is {model_solution.get_solve_status()}. '
                            f'The task setting is {task.save()} and '
                            f'the server setting has available bandwidth of {server.available_bandwidth} and '
                            f'available computation of {server.available_computation} '
                            f'(storage: {server.available_storage})')
        return model_solution.get_value(loading), model_solution.get_value(compute), model_solution.get_value(sending)

    @abstractmethod
    def resource_evaluator(self, task: ElasticTask, server: Server,
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


class SumPercentage(ResourceAllocation):
    """The sum of percentage"""

    def __init__(self):
        ResourceAllocation.__init__(self, 'Percent Sum')

    def resource_evaluator(self, task: ElasticTask, server: Server, loading_speed: int, compute_speed: int,
                           sending_speed: int) -> float:
        """Resource evaluator"""
        return compute_speed / server.available_computation + \
            (loading_speed + sending_speed) / server.available_bandwidth


class SumPowPercentage(ResourceAllocation):
    """The sum of exponential percentages"""

    def __init__(self):
        ResourceAllocation.__init__(self, "Pow percent sum")

    def resource_evaluator(self, task: ElasticTask, server: Server, loading_speed: int, compute_speed: int,
                           sending_speed: int) -> float:
        """Resource evaluator"""
        return (compute_speed / server.available_computation) ** 2 + \
               ((loading_speed + sending_speed) / server.available_bandwidth) ** 2


class SumSpeed(ResourceAllocation):
    """The sum of resource speeds"""

    def __init__(self):
        ResourceAllocation.__init__(self, 'Sum of speeds')

    def resource_evaluator(self, task: ElasticTask, server: Server,
                           loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """Resource evaluator"""
        return loading_speed + compute_speed + sending_speed


class DeadlinePercent(ResourceAllocation):
    """Ratio of speeds divided by deadline"""

    def __init__(self):
        ResourceAllocation.__init__(self, 'Deadline Percent')

    def resource_evaluator(self, task: ElasticTask, server: Server, loading_speed: int, compute_speed: int,
                           sending_speed: int) -> float:
        """Resource evaluator"""
        return (task.required_storage / loading_speed +
                task.required_computation / compute_speed +
                task.required_results_data / sending_speed) / task.deadline


class EvolutionStrategy(ResourceAllocation):
    """Covariance matrix adaption evolution strategy"""

    def __init__(self, name: int, loading_var: Optional[float] = None, compute_var: Optional[float] = None,
                 sending_var: Optional[float] = None):
        ResourceAllocation.__init__(self, f'CMA-ES {name}')

        self.loading_var = loading_var if loading_var else gauss(0, 1)
        self.compute_var = compute_var if compute_var else gauss(0, 1)
        self.sending_var = sending_var if sending_var else gauss(0, 1)

    def resource_evaluator(self, task: ElasticTask, server: Server, loading_speed: int, compute_speed: int,
                           sending_speed: int) -> float:
        """Resource evaluator"""
        return self.loading_var * loading_speed + self.compute_var * compute_speed + self.sending_var * sending_speed


resource_allocation_functions = (
    SumPercentage(),
    SumPowPercentage()
)

max_name_length = max(len(func.name) for func in resource_allocation_functions)
