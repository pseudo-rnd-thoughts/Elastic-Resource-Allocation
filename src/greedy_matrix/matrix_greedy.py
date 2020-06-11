"""Greedy algorithm using a matrix of job and server resource allocation values"""

from __future__ import annotations

from time import time
from typing import List, Tuple

from src.core.core import allocate
from src.core.task import Task
from src.core.result import Result
from src.core.server import Server
from src.greedy_matrix.allocation_value_policy import AllocationValuePolicy


def allocate_resources(job: Task, server: Server, value: AllocationValuePolicy) -> Tuple[float, int, int, int]:
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


def matrix_greedy(jobs: List[Task], servers: List[Server], allocation_value_policy: AllocationValuePolicy,
                  debug_allocation: bool = False, debug_pop: bool = False) -> Result:
    """
    A greedy algorithm that uses the idea of a matrix

    :param jobs: A list of jobs
    :param servers: A list of servers
    :param allocation_value_policy: The value matrix policy
    :param debug_allocation: Debugs the allocation
    :param debug_pop: Debugs the values that are popped
    :return: The results
    """
    start_time = time()

    # Generate the full allocation value matrix
    allocation_value_matrix = {(job, server): allocate_resources(job, server, allocation_value_policy)
                               for job in jobs for server in servers if server.can_run(job)}
    unallocated_jobs = jobs.copy()

    # Loop over the allocation matrix till there are no values left
    while len(allocation_value_matrix):
        (allocated_job, allocated_server), (v, s, w, r) = max(allocation_value_matrix.items(), key=lambda x: x[1][0])
        allocate(allocated_job, s, w, r, allocated_server)
        if debug_allocation:
            print("Task {} on Server {} with value {:.3f}, loading {} compute {} sending {}"
                  .format(allocated_job.name, allocated_server.name, v, s, w, r))

        # Remove the job from the allocation matrix
        for server in servers:
            if (allocated_job, server) in allocation_value_matrix:
                if debug_pop:
                    print("Pop job {} and server {}".format(allocated_job.name, server.name))
                allocation_value_matrix.pop((allocated_job, server))

        # Remove the job from the unallocated jobs and check if the allocated server can now not run any of the jobs
        unallocated_jobs.remove(allocated_job)
        for job in unallocated_jobs:
            # Update the allocation when the server is updated
            if allocated_server.can_run(job):
                allocation_value_matrix[(job, allocated_server)] = allocate_resources(job, allocated_server,
                                                                                      allocation_value_policy)
            # If job cant be run then remove the job
            elif (job, allocated_server) in allocation_value_matrix:
                if debug_pop:
                    print("Pop job {} and server {}".format(job.name, allocated_server.name))
                allocation_value_matrix.pop((job, allocated_server))

    return Result("Matrix Greedy " + allocation_value_policy.name, jobs, servers, solve_time=time() - start_time)
