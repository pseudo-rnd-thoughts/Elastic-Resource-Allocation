"""The greedy algorithm implemtnation"""

from __future__ import annotations
from typing import List

from core.job import Job
from core.result import Result, print_job_values, print_job_allocation
from core.server import Server

from greedy.resource_allocation_policy import ResourceAllocationPolicy, max_name_length as resource_name_length
from greedy.server_selection_policy import ServerSelectionPolicy, max_name_length as server_selection_name_length
from greedy.value_density import ValueDensity, max_name_length as value_density_name_length


def greedy_algorithm(jobs: List[Job], servers: List[Server], value_density: ValueDensity,
                     server_selection_policy: ServerSelectionPolicy,
                     resource_allocation_policy: ResourceAllocationPolicy, job_values_debug: bool = False,
                     job_allocation_debug: bool = False) -> Result:
    """
    A greedy algorithm to allocate jobs to servers aiming to maximise the total utility,
        the models is stored with the servers and jobs so no return is required
    :param jobs: List of jobs
    :param servers: List of servers
    :param value_density: The value density function
    :param server_selection_policy: The selection policy function
    :param resource_allocation_policy: The bid policy function
    :param job_values_debug: The job values debug
    :param job_allocation_debug: The job allocation debug
    """

    # Sorted list of job and value density
    job_values = sorted(((job, value_density.evaluate(job)) for job in jobs), key=lambda jv: jv[1], reverse=True)
    if job_values_debug:
        print_job_values(job_values)

    allocate_jobs([job for job, value in job_values], servers, server_selection_policy, resource_allocation_policy,
                  job_allocation_debug=job_allocation_debug)

    algorithm_name = 'Greedy {}, {}, {}'.format(value_density.name, server_selection_policy.name,
                                                resource_allocation_policy.name)
    return Result(algorithm_name, jobs, servers)


def allocate_jobs(jobs: List[Job], servers: List[Server], server_selection_policy: ServerSelectionPolicy,
                  resource_allocation_policy: ResourceAllocationPolicy, job_allocation_debug: bool = False):
    """

    :param jobs:
    :param servers:
    :param server_selection_policy:
    :param resource_allocation_policy:
    :param job_allocation_debug:
    :return:
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

            # Print the job allocation
            if job_allocation_debug:
                print_job_allocation(job, allocated_server, s, w, r)
