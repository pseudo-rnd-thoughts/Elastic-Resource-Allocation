"""A single shot auction in a centralised way"""

from __future__ import annotations

from time import time
from typing import List, Dict, Tuple

from core.core import allocate
from core.job import Job
from core.model import reset_model
from core.result import Result
from core.server import Server
from greedy.greedy import allocate_jobs
from greedy.resource_allocation_policy import ResourceAllocationPolicy
from greedy.server_selection_policy import ServerSelectionPolicy
from greedy.value_density import ValueDensity


def critical_value_auction(jobs: List[Job], servers: List[Server], value_density: ValueDensity,
                           server_selection_policy: ServerSelectionPolicy,
                           resource_allocation_policy: ResourceAllocationPolicy,
                           debug_initial_allocation: bool = False, debug_critical_value: bool = False) -> Result:
    """
    Implementation of the critical value auction
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param value_density: The value density heuristic
    :param server_selection_policy: The server selection heuristic
    :param resource_allocation_policy: The resource allocation heuristic
    :param debug_initial_allocation: Debug the initial allocation
    :param debug_critical_value: Debug the critical values
    :return:
    """
    start_time = time()
    
    valued_jobs: Dict[Job, float] = {job: value_density.evaluate(job) for job in jobs}
    ranked_jobs: List[Job] = sorted(valued_jobs, key=lambda j: valued_jobs[j], reverse=True)
    
    # Runs the greedy algorithm
    allocate_jobs(ranked_jobs, servers, server_selection_policy, resource_allocation_policy)
    allocation_data: Dict[Job, Tuple[int, int, int, Server]] = {
        job: (job.loading_speed, job.compute_speed, job.sending_speed, job.running_server)
        for job in ranked_jobs if job.running_server
    }
    
    if debug_initial_allocation:
        max_name_len = max(len(job.name) for job in jobs)
        print("{:<{}} | s | w | r | server".format("Job", max_name_len))
        for job, (s, w, r, server) in allocation_data.items():
            print("{:<{}}|{:3f}|{:3f}|{:3f}|{}".format(job, max_name_len, s, w, r, server.name))
    
    reset_model(jobs, servers)
    
    # Loop through each job allocated and find the critical value for the job
    for critical_job in allocation_data.keys():
        # Remove the job from the ranked jobs and save the original position
        critical_pos = ranked_jobs.index(critical_job)
        ranked_jobs.remove(critical_job)
        
        # Loop though the jobs in order checking if the job can be allocated at any point
        for job_pos, job in enumerate(ranked_jobs):
            # If any of the servers can allocate the critical job then allocate the current job to a server
            if any(server.can_run(critical_job) for server in servers):
                server = server_selection_policy.select(job, servers)
                if server:  # There may not be a server that can allocate the job
                    s, w, r = resource_allocation_policy.allocate(job, server)
                    allocate(job, s, w, r, server)
            else:
                # If critical job isn't able to be allocated therefore the last job's density is found
                #   and the inverse of the value density is calculated with the last job's density.
                #   If the job can always run then the price is zero, the default price so no changes need to be made
                critical_job_density = valued_jobs[ranked_jobs[job_pos - 1]]
                critical_job.price = round(value_density.inverse(critical_job, critical_job_density), 3)
                break
        
        if debug_critical_value:
            print("Job {} critical value: {:.3f}".format(critical_job.name, critical_job.price))
        
        # Read the job back into the ranked job in its original position and reset the model but not forgetting the
        #   new critical job's price
        ranked_jobs.insert(critical_pos, critical_job)
        reset_model(jobs, servers, forgot_price=False)
    
    # Allocate the jobs and set the price to the critical value
    for job, (s, w, r, server) in allocation_data.items():
        allocate(job, s, w, r, server)
    
    return Result('Critical Value: {}, {}, {}'
                  .format(value_density.name, server_selection_policy.name, resource_allocation_policy.name),
                  jobs, servers, time() - start_time, show_money=True, value_density=value_density.name,
                  server_selection_policy=server_selection_policy.name,
                  resource_allocation_policy=resource_allocation_policy.name)
