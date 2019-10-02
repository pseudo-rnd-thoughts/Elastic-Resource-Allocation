"""A single shot auction in a centralised way"""

from __future__ import annotations

from math import floor
from time import time
from typing import List

from core.core import print_job_values
from core.job import Job
from core.model import reset_model
from core.result import Result
from core.server import Server
from greedy.greedy import allocate_jobs
from greedy.resource_allocation_policy import ResourceAllocationPolicy
from greedy.server_selection_policy import ServerSelectionPolicy
from greedy.value_density import ValueDensity


def find_critical_value(job: Job, sorted_jobs: List[Job], servers: List[Server],
                        server_selection_policy: ServerSelectionPolicy,
                        resource_allocation_policy: ResourceAllocationPolicy,
                        debug_bound: bool = False, debug_price: bool = False) -> float:
    """
    Calculates the critical values of the job
    :param job: The job to find the critical value
    :param sorted_jobs: A sorted list of jobs
    :param servers: A list of servers
    :param server_selection_policy: The server selection policy
    :param resource_allocation_policy: The resource allocation policy
    :param debug_bound: Debugs the bound that the job position is being tested at
    :param debug_price: Debugs the final price
    :return: The results
    """
    # The upper and lower bound index in the job list that is sorted by value
    upper_bound, lower_bound = sorted_jobs.index(job), len(sorted_jobs) - 1
    jobs = sorted_jobs.copy()

    if debug_bound:
        print("\nJob: {} - Initial index: {}".format(job.name, upper_bound))

    # Loop till the two bounds are equal to each other (this is a speical implementation of the binary search algo)
    while upper_bound < lower_bound:
        reset_model(jobs, servers)

        # Find a test position between the two bounds and insert the job into that position in the list
        test_pos = floor((upper_bound + lower_bound) / 2)
        jobs.remove(job)
        jobs.insert(test_pos, job)

        # Run the greedy algorithm, allocating the jobs
        allocate_jobs(jobs, servers, server_selection_policy, resource_allocation_policy)

        # Dependant on if the job is allocated then change the upper or lower bound
        if job.running_server:
            upper_bound = test_pos + 1
            if debug_bound:
                print("Allocated - New Upper bound: {}, Lower bound: {}".format(upper_bound, lower_bound))
        else:
            lower_bound = test_pos - 1
            if debug_bound:
                print("Not Allocated - Upper bound: {}, New Lower bound: {}".format(upper_bound, lower_bound))

    # Special case where the job is the last index in the list and is still allocated
    if upper_bound == len(sorted_jobs) - 1:
        if debug_price:
            print("Price: 0")
        return 0
    else:
        # Else find the job value of the job below on the list
        if debug_price:
            print("Price: {}".format(sorted_jobs[upper_bound].value))
        return sorted_jobs[upper_bound].value


def critical_value_auction(jobs: List[Job], servers: List[Server],
                           value_density: ValueDensity, server_selection_policy: ServerSelectionPolicy,
                           resource_allocation_policy: ResourceAllocationPolicy,
                           debug_job_value: bool = False, debug_greedy_allocation: bool = False,
                           debug_critical_bound: bool = False, debug_critical_value: bool = False) -> Result:
    """
    Critical value auction
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param value_density: The value density function
    :param server_selection_policy: The server selection policy
    :param resource_allocation_policy: The resource allocation policy
    :param debug_job_value: Debug the job value ordering
    :param debug_greedy_allocation: Debug the job allocation
    :param debug_critical_bound: Debug the bound for each job
    :param debug_critical_value: Debug the price for each job
    :return: The results
    """
    start_time = time()

    # Sort the list according to a value density function
    valued_jobs = sorted((job for job in jobs), key=lambda job: value_density.evaluate(job), reverse=True)
    if debug_job_value:
        print_job_values(sorted(((job, value_density.evaluate(job)) for job in jobs),
                                key=lambda jv: jv[1], reverse=True))

    # Find the allocation of jobs with the list sorted normally
    allocate_jobs(valued_jobs, servers, server_selection_policy, resource_allocation_policy,
                  debug_allocation=debug_greedy_allocation)
    allocated_jobs = {job: (job.loading_speed, job.compute_speed, job.sending_speed, job.running_server)
                      for job in valued_jobs if job.running_server}

    # Find the job's critical value of the allocated jobs

    job_critical_values = {}
    for job in allocated_jobs.keys():
        job_critical_values[job] = find_critical_value(job, valued_jobs, servers, server_selection_policy,
                                                       resource_allocation_policy, debug_bound=debug_critical_bound,
                                                       debug_price=debug_critical_value)

    reset_model(jobs, servers)

    # Allocate the jobs and set the price to the critical value
    for job in allocated_jobs.keys():
        s, w, r, server = allocated_jobs[job]
        price = job_critical_values[job]
        job.allocate(s, w, r, server, price=price)
        server.allocate_job(job)

    return Result('Critical Value {}, {}, {}'.format(value_density.name, server_selection_policy.name,
                                                     resource_allocation_policy.name),
                  jobs, servers, time() - start_time, show_money=True,
                  value_density=value_density.name,
                  server_selection_policy=server_selection_policy.name,
                  resource_allocation_policy=resource_allocation_policy.name)
