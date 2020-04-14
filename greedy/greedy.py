"""The greedy algorithm implementation"""

from __future__ import annotations

from time import time
from typing import List

from core.core import print_job_allocation, print_job_values
from core.job import Job
from core.result import Result
from core.server import Server
from greedy.resource_allocation_policy import ResourceAllocationPolicy
from greedy.server_selection_policy import ServerSelectionPolicy
from greedy.value_density import ValueDensity


def greedy_algorithm(jobs: List[Job], servers: List[Server], value_density: ValueDensity,
                     server_selection_policy: ServerSelectionPolicy,
                     resource_allocation_policy: ResourceAllocationPolicy, debug_job_values: bool = False,
                     debug_job_allocation: bool = False) -> Result:
    """
    A greedy algorithm to allocate jobs to servers aiming to maximise the total utility,
        the models is stored with the servers and jobs so no return is required
    :param jobs: List of jobs
    :param servers: List of servers
    :param value_density: The value density function
    :param server_selection_policy: The selection policy function
    :param resource_allocation_policy: The bid policy function
    :param debug_job_values: The job values debug
    :param debug_job_allocation: The job allocation debug
    """
    start_time = time()

    # Sorted list of job and value density
    job_values = sorted((job for job in jobs), key=lambda job: value_density.evaluate(job), reverse=True)
    if debug_job_values:
        print_job_values(sorted(((job, value_density.evaluate(job)) for job in jobs),
                                key=lambda jv: jv[1], reverse=True))

    # Run the allocation of the job with the sorted job by value
    allocate_jobs(job_values, servers, server_selection_policy, resource_allocation_policy,
                  debug_allocation=debug_job_allocation)

    # The algorithm name
    algorithm_name = 'Greedy {}, {}, {}'.format(value_density.name, server_selection_policy.name,
                                                resource_allocation_policy.name)
    return Result(algorithm_name, jobs, servers, time() - start_time,
                  value_density=value_density.name, server_selection_policy=server_selection_policy.name,
                  resource_allocation_policy=resource_allocation_policy.name)


def allocate_jobs(jobs: List[Job], servers: List[Server], server_selection_policy: ServerSelectionPolicy,
                  resource_allocation_policy: ResourceAllocationPolicy, debug_allocation: bool = False):
    """
    Allocate the jobs to the servers based on the server selection policy and resource allocation policies
    :param jobs: The list of jobs
    :param servers: The list of servers
    :param server_selection_policy: The server selection policy
    :param resource_allocation_policy: The resource allocation policy
    :param debug_allocation: The job allocation debug
    """

    # Loop through all of the job in order of values
    for job in jobs:
        # Allocate the server using the allocation policy function
        allocated_server = server_selection_policy.select(job, servers)

        # If an optimal server is found then calculate the bid allocation function
        if allocated_server:
            s, w, r = resource_allocation_policy.allocate(job, allocated_server)
            job.allocate(s, w, r, allocated_server)
            allocated_server.allocate_job(job)

    if debug_allocation:
        print_job_allocation(jobs)
