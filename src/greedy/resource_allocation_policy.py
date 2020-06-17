"""Bid policy functions"""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import exp
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Tuple

    from core.task import Task
    from core.server import Server


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
        return min(((s, w, r)
                    for s in range(1, server.available_bandwidth + 1)
                    for w in range(1, server.available_computation + 1)
                    for r in range(1, server.available_bandwidth - s + 1)
                    if task.required_storage * w * r + s * task.required_computation * r +
                    s * w * task.required_results_data <= task.deadline * s * w * r),
                   key=lambda bid: self.resource_evaluator(task, server, bid[0], bid[1], bid[2]))

    @abstractmethod
    def resource_evaluator(self, task: Task, server: Server,
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
        ResourceAllocationPolicy.__init__(self, 'Percentage Sum')

    def resource_evaluator(self, task: Task, server: Server, loading_speed: int, compute_speed: int,
                           sending_speed: int) -> float:
        """Resource evaluator"""
        return compute_speed / server.available_computation + \
            (loading_speed + sending_speed) / server.available_bandwidth


class SumExpPercentage(ResourceAllocationPolicy):
    """The sum of exponential percentages"""

    def __init__(self):
        ResourceAllocationPolicy.__init__(self, "Expo percentage sum")

    def resource_evaluator(self, task: Task, server: Server, loading_speed: int, compute_speed: int,
                           sending_speed: int) -> float:
        """Resource evaluator"""
        return exp(compute_speed / server.available_computation) + \
            exp((loading_speed + sending_speed) / server.available_bandwidth)


class SumSpeed(ResourceAllocationPolicy):
    """The sum of resource speeds"""

    def __init__(self):
        ResourceAllocationPolicy.__init__(self, 'Sum of speeds')

    def resource_evaluator(self, task: Task, server: Server,
                           loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """Resource evaluator"""
        return loading_speed + compute_speed + sending_speed


class DeadlinePercent(ResourceAllocationPolicy):
    """Ratio of speeds divided by deadline"""

    def __init__(self):
        ResourceAllocationPolicy.__init__(self, 'Deadline Percent')

    def resource_evaluator(self, task: Task, server: Server, loading_speed: int, compute_speed: int,
                           sending_speed: int) -> float:
        """Resource evaluator"""
        return (task.required_storage / loading_speed +
                task.required_computation / compute_speed +
                task.required_results_data / sending_speed) / task.deadline


policies = (
    SumPercentage(),
    SumExpPercentage(),
    SumSpeed()
)

max_name_length = max(len(policy.name) for policy in policies)
