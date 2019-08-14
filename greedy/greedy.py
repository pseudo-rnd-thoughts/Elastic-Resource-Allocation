"""The greedy algorithm implemtnation"""

from __future__ import annotations
from typing import List

from core.job import Job
from core.result import Result, print_job_values, print_job_allocation
from core.server import Server
from greedy.resource_allocation_policy import ResourceAllocationPolicy
from greedy.server_selection_policy import ServerSelectionPolicy
from greedy.value_density import ValueDensity


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

    # Loop through all of the job in order of values
    for job, _ in job_values:
        # Allocate the server using the allocation policy function
        allocated_server = server_selection_policy.select(job, servers)

        # If an optimal server is found then calculate the bid allocation function
        if allocated_server:
            value, (s, w, r) = resource_allocation_policy.allocate(job, allocated_server)
            job.allocate(s, w, r, allocated_server)
            allocated_server.allocate_job(s, w, r, job)

            # Print the job allocation
            if job_allocation_debug:
                print_job_allocation(job, allocated_server, s, w, r)

    return Result("{}, {}, {}".format(value_density.name, server_selection_policy.name,
                                      resource_allocation_policy.name), jobs, servers)
