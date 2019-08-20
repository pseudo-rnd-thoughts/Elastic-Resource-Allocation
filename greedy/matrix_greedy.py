""""""

from __future__ import annotations
from typing import List
from abc import abstractmethod

from core.job import Job
from core.server import Server
from core.result import Result


class MatrixValue(object):
    def __init__(self, name: str):
        self.name: str = name
        
    @abstractmethod
    def evaluate(self, job: Job, server: Server, s: int, w: int, r: int):
        pass
    

class SumServerUsage(MatrixValue):
    def __init__(self):
        super().__init__("Sum Usage")
        
    def evaluate(self, job: Job, server: Server, s: int, w: int, r: int):
        return job.utility * ((server.available_storage - job.required_storage) +
                              (server.available_computation - w) +
                              (server.available_bandwidth - (s + r)))


class SumServerPercentage(MatrixValue):
    def __init__(self):
        super().__init__("Sum Percentage")
    
    def evaluate(self, job: Job, server: Server, s: int, w: int, r: int):
        return job.utility * ((server.available_storage - job.required_storage) / server.available_storage +
                              (server.available_computation - w) / server.available_computation +
                              (server.available_bandwidth - (s + r)) / server.available_bandwidth)


class ProductServerPercentage(MatrixValue):
    def __init__(self):
        super().__init__("Product Percentage")
        
    def evaluate(self, job: Job, server: Server, s: int, w: int, r: int):
        return job.utility * \
               ((server.available_storage - job.required_storage) / server.available_storage) * \
               ((server.available_computation - w) / server.available_computation) * \
               ((server.available_bandwidth - (s + r)) / server.available_bandwidth)


def allocate_resources(job: Job, server: Server, value: MatrixValue):
    return max(((value.evaluate(job, server, s, w, r), s, w, r)
                for s in range(1, server.available_bandwidth + 1)
                for w in range(1, server.available_computation + 1)
                for r in range(1, server.available_bandwidth - s + 1)
                if job.required_storage * w * r + s * job.required_computation * r +
                s * w * job.required_results_data <= job.deadline * s * w * r), key=lambda x: x[0])


def matrix_greedy(jobs: List[Job], servers: List[Server], matrix_policy: MatrixValue):
    unallocated_jobs = jobs.copy()
    while unallocated_jobs:
        value_matrix = []
        for job in unallocated_jobs:
            for server in servers:
                if server.can_run(job):
                    value, s, w, r = allocate_resources(job, server, matrix_policy)
                    value_matrix.append((value, job, server, s, w, r))
                    
        if value_matrix:
            value, job, server, s, w, r = max(value_matrix, key=lambda x: x[0])
            job.allocate(s, w, r, server)
            server.allocate_job(job)
            unallocated_jobs.remove(job)
        else:
            break

    return Result("Matrix Greedy", jobs, servers)


policies = (
    SumServerUsage(),
    SumServerPercentage(),
    ProductServerPercentage()
)
