"""Matrix policies"""

from __future__ import annotations
from abc import abstractmethod
from math import exp

from core.job import Job
from core.server import Server


class MatrixPolicy(object):
    def __init__(self, name: str):
        self.name: str = name
    
    @abstractmethod
    def evaluate(self, job: Job, server: Server, s: int, w: int, r: int):
        pass


class SumServerUsage(MatrixPolicy):
    def __init__(self):
        super().__init__("Sum Usage")
    
    def evaluate(self, job: Job, server: Server, s: int, w: int, r: int):
        return job.utility * ((server.available_storage - job.required_storage) +
                              (server.available_computation - w) +
                              (server.available_bandwidth - (s + r)))


class SumServerPercentage(MatrixPolicy):
    def __init__(self):
        super().__init__("Sum Percentage")
    
    def evaluate(self, job: Job, server: Server, s: int, w: int, r: int):
        return job.utility * ((server.available_storage - job.required_storage) / server.available_storage +
                              (server.available_computation - w) / server.available_computation +
                              (server.available_bandwidth - (s + r)) / server.available_bandwidth)


class SumExpServerPercentage(MatrixPolicy):
    def __init__(self):
        super().__init__("Sum Exp Percentage")
    
    def evaluate(self, job: Job, server: Server, s: int, w: int, r: int):
        return job.utility * (exp((server.available_storage - job.required_storage) / server.available_storage) +
                              exp((server.available_computation - w) / server.available_computation) +
                              exp((server.available_bandwidth - (s + r)) / server.available_bandwidth))


class SumExp3ServerPercentage(MatrixPolicy):
    def __init__(self):
        super().__init__("Sum Exp^3 Percentage")
    
    def evaluate(self, job: Job, server: Server, s: int, w: int, r: int):
        return job.utility * (exp(((server.available_storage - job.required_storage) / server.available_storage) ** 3) +
                              exp(((server.available_computation - w) / server.available_computation) ** 3) +
                              exp(((server.available_bandwidth - (s + r)) / server.available_bandwidth) ** 3))
    

policies = (
    SumServerUsage(),
    SumServerPercentage(),
    ProductServerPercentage(),
    SumExpServerPercentage(),
    SumExp3ServerPercentage()
)
