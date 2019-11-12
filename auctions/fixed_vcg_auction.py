"""Combinatorial Double Auction"""

from __future__ import annotations

from time import time
from typing import List, Dict, Optional

from branch_bound.branch_bound import branch_bound_algorithm
from branch_bound.feasibility_allocations import fixed_feasible_allocation
from core.core import allocate, list_copy_remove
from core.job import Job
from core.model import reset_model
from core.result import Result
from core.server import Server
from core.fixed_job import FixedJob


def fixed_vcg_auction(jobs: List[FixedJob], servers: List[Server],
                      debug_running: bool = False, debug_results: bool = False) -> Optional[Result]:
    """
    Combinatorial Double auction solved through VCG auction algorithm
    :param jobs: a list of jobs
    :param servers: a list of servers
    :param debug_running: debug the running
    :param debug_results: debug the results
    :return: the results
    """
    start_time = time()

    # Price information
    job_prices: Dict[Job, float] = {}

    # Find the optimal solution
    if debug_running:
        print("Finding optimal")
    optimal_solution = branch_bound_algorithm(jobs, servers, fixed_feasible_allocation)
    if optimal_solution is None:
        return None
    elif debug_results:
        print("Optimal total utility: {}".format(optimal_solution))

    # Save the job and server information from the optimal solution
    allocated_jobs = [job for job in jobs if job.running_server]
    job_allocation: Dict[Job, Server] = {job: job.running_server for job in jobs}

    if debug_running:
        print("Allocated jobs: {}".format(", ".join([job.name for job in allocated_jobs])))

    # For each allocated job, find the sum of values if the job doesnt exist
    for job in allocated_jobs:
        # Reset the model and remove the job from the job list
        reset_model(jobs, servers)
        jobs_prime = list_copy_remove(jobs, job)

        # Find the optimal solution where the job doesnt exist
        if debug_running:
            print("Solving for without {} job".format(job.name))
        optimal_prime = branch_bound_algorithm(jobs_prime, servers, fixed_feasible_allocation)
        if optimal_prime is None:
            return None
        else:
            job_prices[job] = optimal_solution.sum_value - optimal_prime.sum_value
            if debug_results:
                print("Job {}: £{:.1f}, Value: {} ".format(job.name, job_prices[job], job.value))

    # Resets all of the jobs and servers and allocates all of their info from the original optimal solution
    reset_model(jobs, servers)
    for job in allocated_jobs:
        allocate(job, -1, -1, -1, job_allocation[job], job_prices[job])

    return Result('vcg', jobs, servers, time() - start_time, show_money=True)
