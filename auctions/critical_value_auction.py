"""A single shot auction in a centralised way"""

from __future__ import annotations

import operator
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


def calculate_critical_value(critical_job: Job, ranked_jobs: List[Job], servers: List[Server],
                             value_density: ValueDensity, server_selection_policy: ServerSelectionPolicy,
                             resource_allocation_policy: ResourceAllocationPolicy,
                             debug_bound: bool = False) -> float:
    """
    Calculates the critical values of the job
    :param critical_job: The job to find the critical value
    :param ranked_jobs: A sorted list of jobs
    :param servers: A list of servers
    :param value_density: The value density
    :param server_selection_policy: The server selection policy
    :param resource_allocation_policy: The resource allocation policy
    :param debug_bound: Debugs the bound that the job position is being tested at
    :return: The results
    """
    for pos in range(ranked_jobs.index(critical_job) + 1, len(ranked_jobs) - 1):
        reset_model(ranked_jobs, servers)

        ranked_jobs.remove(critical_job)
        ranked_jobs.insert(pos, critical_job)

        # Run the greedy algorithm, allocating the jobs
        allocate_jobs(ranked_jobs, servers, server_selection_policy, resource_allocation_policy)

        if critical_job.running_server:
            if debug_bound:
                print("Job allocated to server " + critical_job.running_server.name + " at position " + str(pos))
        else:
            density = value_density.evaluate(ranked_jobs[pos - 1])
            return value_density.inverse(critical_job, density)
    return 0


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
    allocation_data = {job: (job.loading_speed, job.compute_speed, job.sending_speed, job.running_server)
                       for job in valued_jobs if job.running_server}

    # Find the job's critical value of the allocated jobs

    job_critical_values = {}
    for job in allocation_data.keys():
        job_critical_values[job] = calculate_critical_value(job, valued_jobs, servers, value_density,
                                                            server_selection_policy, resource_allocation_policy,
                                                            debug_bound=debug_critical_bound)
        if debug_critical_value:
            print("Job {} critical value = {:.3f}".format(job.name, job_critical_values[job]))

    reset_model(jobs, servers)
    # Allocate the jobs and set the price to the critical value
    for job, (s, w, r, server) in allocation_data.items():
        price = job_critical_values[job]
        job.allocate(s, w, r, server, price=price)
        server.allocate_job(job)

    return Result('Critical Value {}, {}, {}'
                  .format(value_density.name, server_selection_policy.name, resource_allocation_policy.name),
                  jobs, servers, time() - start_time, show_money=True, value_density=value_density.name,
                  server_selection_policy=server_selection_policy.name,
                  resource_allocation_policy=resource_allocation_policy.name)


def cv_auction(jobs: List[Job], servers: List[Server], value_density: ValueDensity,
               server_selection_policy: ServerSelectionPolicy, resource_allocation_policy: ResourceAllocationPolicy):
    start_time = time()

    valued_jobs = {job: value_density.evaluate(job) for job in jobs}
    ranked_jobs = sorted(valued_jobs.items(), key=operator.itemgetter(1), reverse=True)

    # Runs the greedy algorithm
    allocate_jobs(ranked_jobs, servers, server_selection_policy, resource_allocation_policy)
    allocation_data = {job: (job.loading_speed, job.compute_speed, job.sending_speed, job.running_server)
                       for job in ranked_jobs if job.running_server}
    reset_model(jobs, servers)
    
    for critical_job in allocation_data.keys():
        critical_pos = ranked_jobs.index(critical_job)
        ranked_jobs.remove(critical_job)

        for job_pos in range(len(ranked_jobs)):
            if any(server.can_run(critical_job) for server in servers):
                server = server_selection_policy.select(jobs[job_pos], servers)
                resource_allocation_policy.allocate(jobs[job_pos], server)
            else:
                if job_pos == 0:
                    critical_job.price = 0
                elif job_pos < len(jobs) - 1:
                    critical_job.price = value_density.inverse(critical_job, valued_jobs[ranked_jobs[job_pos - 1]])

        ranked_jobs.insert(critical_pos, critical_job)
        reset_model(jobs, servers, forgot_price=False)

    reset_model(jobs, servers)
    # Allocate the jobs and set the price to the critical value
    for job, (s, w, r, server) in allocation_data.items():
        job.allocate(s, w, r, server)
        server.allocate_job(job)

    return Result('Critical Value {}, {}, {}'
                  .format(value_density.name, server_selection_policy.name, resource_allocation_policy.name),
                  jobs, servers, time() - start_time, show_money=True, value_density=value_density.name,
                  server_selection_policy=server_selection_policy.name,
                  resource_allocation_policy=resource_allocation_policy.name)
