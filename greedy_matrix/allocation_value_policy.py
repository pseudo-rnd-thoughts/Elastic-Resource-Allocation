"""Matrix policies"""

from __future__ import annotations
from abc import abstractmethod
from math import exp

from core.job import Job
from core.server import Server


class AllocationValuePolicy(object):
    """
    Allocation Value Policy
    """
    def __init__(self, name: str):
        self.name: str = name
    
    @abstractmethod
    def evaluate(self, job: Job, server: Server, loading_speed: int, compute_speed: int, sending_speed: int):
        """
        Evaluation with all information
        :param job: A job
        :param server: A server
        :param loading_speed: A loading speed
        :param compute_speed: A compute speed
        :param sending_speed: A sending speed
        :return: The value of the information
        """
        pass


class SumServerUsage(AllocationValuePolicy):
    """
    Sum of servers usage after allocation
    """
    def __init__(self):
        super().__init__("Sum Usage")
    
    def evaluate(self, job: Job, server: Server, loading_speed: int, compute_speed: int, sending_speed: int):
        return job.utility * ((server.available_storage - job.required_storage) +
                              (server.available_computation - compute_speed) +
                              (server.available_bandwidth - (loading_speed + sending_speed)))


class SumServerPercentage(AllocationValuePolicy):
    """
    Sum of server usage percentage of available resources
    """
    def __init__(self):
        super().__init__("Sum Percentage")
    
    def evaluate(self, job: Job, server: Server, loading_speed: int, compute_speed: int, sending_speed: int):
        return job.utility * \
               ((server.available_storage - job.required_storage) / server.available_storage +
                (server.available_computation - compute_speed) / server.available_computation +
                (server.available_bandwidth - (loading_speed + sending_speed)) / server.available_bandwidth)


class SumServerMaxPercentage(AllocationValuePolicy):
    """
    Sum of server usage percentage of max resources
    """
    def __init__(self):
        super().__init__("Sum Percentage")
    
    def evaluate(self, job: Job, server: Server, loading_speed: int, compute_speed: int, sending_speed: int):
        return job.utility * ((server.available_storage - job.required_storage) / server.max_storage +
                              (server.available_computation - compute_speed) / server.max_computation +
                              (server.available_bandwidth - (loading_speed + sending_speed)) / server.max_bandwidth)
    

class SumExpServerPercentage(AllocationValuePolicy):
    """
    Sum of exponential usage percentage of available resources
    """
    def __init__(self):
        super().__init__("Sum Exp Percentage")
    
    def evaluate(self, job: Job, server: Server, loading_speed: int, compute_speed: int, sending_speed: int):
        return job.utility * \
               (exp((server.available_storage - job.required_storage) / server.available_storage) +
                exp((server.available_computation - compute_speed) / server.available_computation) +
                exp((server.available_bandwidth - (loading_speed + sending_speed)) / server.available_bandwidth))


class SumExp3ServerPercentage(AllocationValuePolicy):
    """
    Sum of the cube of the exponential usage percentage of available resources
    """
    def __init__(self):
        super().__init__("Sum Exp^3 Percentage")
    
    def evaluate(self, job: Job, server: Server, loading_speed: int, compute_speed: int, sending_speed: int):
        return job.utility * \
               (exp(((server.available_storage - job.required_storage) / server.available_storage) ** 3) +
                exp(((server.available_computation - compute_speed) / server.available_computation) ** 3) +
                exp(((server.available_bandwidth - (loading_speed + sending_speed)) / server.available_bandwidth) ** 3))
    

policies = (
    SumServerUsage(),
    SumServerPercentage(),
    SumServerMaxPercentage(),
    SumExpServerPercentage(),
    SumExp3ServerPercentage()
)
