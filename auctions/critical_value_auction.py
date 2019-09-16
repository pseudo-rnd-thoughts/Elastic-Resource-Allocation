"""A single shot auction in a centralised way"""

from __future__ import annotations

from typing import List
from math import floor

from core.job import Job
from core.result import Result
from core.server import Server

from greedy.greedy import allocate_jobs
from greedy.resource_allocation_policy import ResourceAllocationPolicy
from greedy.server_selection_policy import ServerSelectionPolicy
from greedy.value_density import ValueDensity


def calculate_crtical_value(job: Job, sorted_jobs: List[Job], servers: List[Server],
                            server_selection_policy: ServerSelectionPolicy,
                            resource_allocation_policy: ResourceAllocationPolicy) -> float:
    """
    Calculates the critical values of the job
    :param job: The job to find the critical value
    :param sorted_jobs: A sorted list of jobs
    :param servers: A list of servers
    :param server_selection_policy: The server selection policy
    :param resource_allocation_policy: The resource allocation policy
    :return:
    """
    upper_bound, lower_bound = sorted_jobs.index(job), len(sorted_jobs) - 1
    jobs = sorted_jobs.copy()

    while upper_bound != lower_bound:
        test_pos = floor((upper_bound + lower_bound) / 2)
        jobs.remove(job)
        jobs.insert(test_pos, job)

        allocate_jobs(jobs, servers, server_selection_policy, resource_allocation_policy)

        if job.running_server:
            upper_bound = test_pos + 1
        else:
            lower_bound = test_pos - 1

    if upper_bound == len(sorted_jobs) - 1:
        return 0
    else:
        return sorted_jobs[upper_bound].value


def critical_value_auction(jobs: List[Job], servers: List[Server],
                           value_density: ValueDensity, server_selection_policy: ServerSelectionPolicy,
                           resource_allocation_policy: ResourceAllocationPolicy) -> Result:
    """
    Critical value auction
    :param jobs: A list of jobs
    :param servers: A list of serveres
    :param value_density: The value density function
    :param server_selection_policy: The server selection policy
    :param resource_allocation_policy: The resource allocation policy
    :return: The results
    """

    valued_jobs = sorted((job for job in jobs), key=lambda job: value_density.evaluate(job), reverse=True)
    allocate_jobs(valued_jobs, servers, server_selection_policy, resource_allocation_policy)

    allocated_jobs = {job: (job.loading_speed, job.compute_speed, job.sending_speed, job.running_server)
                      for job in jobs}
    job_critical_values = {
        job: calculate_crtical_value(job, valued_jobs, servers, server_selection_policy, resource_allocation_policy)
        for job in allocated_jobs.keys()
    }

    for job in jobs:
        job.reset_allocation()
    for server in servers:
        server.reset_allocations()

    for job in allocated_jobs.keys():
        s, w, r, server = allocated_jobs[job]
        price = job_critical_values[job]
        job.allocate(s, w, r, server, price=price)
        server.allocate_job(job)

    return Result('Critical Value', jobs, servers, show_money=True)
