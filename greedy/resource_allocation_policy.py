"""Bid policy functions"""

from __future__ import annotations
from abc import ABC, abstractmethod
from math import exp
from typing import Tuple, Generator

from core.job import Job
from core.server import Server

from docplex.mp.model import Model

Speed = int


class ResourceAllocationPolicy(ABC):
    """Resource Allocation Policy class that is inherited with each option"""

    def __init__(self, name):
        self.name = name

    def possible_bids(self, job: Job, server: Server) -> Generator[Tuple[float, Tuple[Speed, Speed, Speed]]]:
        """
        Calculates all of the possible bids that could be made
        TODO optimise searching through kkt maths
        :param job: The job
        :param server: The allocated server
        :return: A list of tuples of possible resource speeds
        """
        return ((self.resource_evaluator(job, server, s, w, r), (s, w, r))
                for s in range(1, server.available_bandwidth + 1)
                for w in range(1, server.available_computation + 1)
                for r in range(1, server.available_bandwidth - s + 1)
                if job.required_storage / s + job.required_computation / w + job.required_results_data / r
                <= job.deadline)

    def allocate(self, job: Job, server: Server) -> Tuple[float, Tuple[Speed, Speed, Speed]]:
        """
        Determines the resource speed for the job on the server but finding the smallest
        :param job: The job
        :param server: The server
        :return: A tuple of resource speeds
        """
        return min(self.possible_bids(job, server), key=lambda bid: bid[0])

    @abstractmethod
    def resource_evaluator(self, job: Job, server: Server,
                           loading_speed: Speed, compute_speed: Speed, sending_speed: Speed) -> float:
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
        super().__init__("Sum of server percentage usage")

    def resource_evaluator(self, job: Job, server: Server, loading_speed: Speed, compute_speed: Speed,
                           sending_speed: Speed) -> float:
        """Resource evaluator"""
        return loading_speed / server.available_storage + \
            compute_speed / server.available_computation + \
            sending_speed / server.available_bandwidth


class SumExpPercentage(ResourceAllocationPolicy):
    """The sum of exponential percentages"""

    def __init__(self):
        super().__init__("Sum of exponential server percentage usage")

    def resource_evaluator(self, job: Job, server: Server, loading_speed: Speed, compute_speed: Speed,
                           sending_speed: Speed) -> float:
        """Resource evaluator"""
        return exp(loading_speed / server.available_storage) + \
            exp(compute_speed / server.available_computation) + \
            exp(sending_speed / server.available_bandwidth)


class SumSpeeds(ResourceAllocationPolicy):
    """The sum of resource speeds"""

    def __init__(self):
        super().__init__("Sum of resource speeds")

    def resource_evaluator(self, job: Job, server: Server, loading_speed: Speed, compute_speed: Speed,
                           sending_speed: Speed) -> float:
        """Resource evaluator"""
        return loading_speed + compute_speed + sending_speed


policies = (
    SumPercentage(),
    SumExpPercentage(),
    SumSpeeds()
)
