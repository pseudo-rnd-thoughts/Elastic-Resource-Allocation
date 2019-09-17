"""Greedy algorithm using a matrix of job and server resource allocation values"""

from __future__ import annotations

from typing import List, Tuple
from time import time

from core.job import Job
from core.result import Result
from core.server import Server

from greedy_matrix.allocation_value_policy import AllocationValuePolicy


def allocate_resources(job: Job, server: Server, value: AllocationValuePolicy) -> Tuple[float, int, int, int]:
    """
    Calculates the value of a server job allocation with the resources allocated
    :param job: A job
    :param server: A server
    :param value: The value policy
    :return: The tuple of values and resource allocations
    """
    return max(((value.evaluate(job, server, s, w, r), s, w, r)
                for s in range(1, server.available_bandwidth + 1)
                for w in range(1, server.available_computation + 1)
                for r in range(1, server.available_bandwidth - s + 1)
                if job.required_storage * w * r + s * job.required_computation * r +
                s * w * job.required_results_data <= job.deadline * s * w * r), key=lambda x: x[0])


def matrix_greedy(jobs: List[Job], servers: List[Server], allocation_value_policy: AllocationValuePolicy) -> Result:
    """
    A greedy algorithm that uses the idea of a matrix
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param allocation_value_policy: The value matrix policy
    :return: The results
    """
    allocation_value_matrix = {(job, server): allocate_resources(job, server, allocation_value_policy)
                               for job in jobs for server in servers}
    unallocated_jobs = jobs.copy()

    start_time = time()
    while len(allocation_value_matrix):
        (allocated_job, allocated_server), (value, s, w, r) = max(allocation_value_matrix, key=lambda x: x[0][0])

        allocated_job.allocate(s, w, r, allocated_server)
        allocated_server.allocated_job(allocated_job)

        for job in unallocated_jobs:
            allocation_value_matrix.pop((job, allocated_server))
            if allocated_server.can_run(job) is False:
                allocation_value_matrix.pop((job, allocated_server))
        for server in servers:
            allocation_value_matrix.pop((allocated_job, server))

    return Result("Matrix Greedy " + allocation_value_policy.name, jobs, servers, solve_time=time()-start_time)
