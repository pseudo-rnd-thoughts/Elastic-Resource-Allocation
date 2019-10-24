"""Fixed Job class"""

from __future__ import annotations

from abc import abstractmethod, ABC
from typing import List

from core.job import Job
from core.server import Server


class FixedJob(Job):
    """Job with a fixing resource usage speed"""

    def __init__(self, job: Job, servers: List[Server], fixed_value: FixedValue):
        super().__init__("fixed " + job.name, job.required_storage, job.required_computation, job.required_results_data,
                         job.value, job.deadline)
        self.original_job = job
        self.loading_speed, self.compute_speed, self.sending_speed = min(
            ((s, w, r)
             for s in range(1, max(server.max_bandwidth for server in servers))
             for w in range(1, max(server.max_computation for server in servers))
             for r in range(1, max(server.max_bandwidth for server in servers))
             if job.required_storage * w * r + s * job.required_computation * r +
             s * w * job.required_results_data <= job.deadline * s * w * r),
            key=lambda speed: fixed_value.evaluate(speed[0], speed[1], speed[2]))

    def allocate(self, loading_speed: int, compute_speed: int, sending_speed: int, running_server: Server,
                 price: float = 0):
        """
        Overrides the allocate function from job to just allocate the running server and the price
        :param loading_speed: Ignored
        :param compute_speed: Ignored
        :param sending_speed: Ignored
        :param running_server: The server the job is running on
        :param price: The price of the job
        """
        assert self.running_server is None

        self.running_server = running_server
        self.price = price

    def reset_allocation(self):
        """
        Overrides the reset_allocation function from job to just change the server not resource speeds
        """
        self.running_server = None


class FixedValue(ABC):
    """
    Fixed Value policy for the fixed job to select the speed
    """

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def evaluate(self, loading_speed: int, compute_speed: int, sending_speed: int) -> int:
        """
        Evaluate how good certain speeds
        :param loading_speed: Loading speed
        :param compute_speed: Compute speed
        :param sending_speed: Sending speed
        :return: How good it is
        """
        pass


class FixedSumSpeeds(FixedValue):
    """Fixed sum of speeds"""

    def __init__(self):
        super().__init__("Sum speeds")

    def evaluate(self, loading_speed: int, compute_speed: int, sending_speed: int) -> int:
        """Evaluation of how good it is"""
        return loading_speed + compute_speed + sending_speed

# TODO add more fixed value classes
