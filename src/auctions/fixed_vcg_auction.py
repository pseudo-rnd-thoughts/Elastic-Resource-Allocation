"""Combinatorial Double Auction"""

from __future__ import annotations

from time import time
from typing import List, Dict, Optional

from src.core.core import allocate, list_copy_remove
from src.core.fixed_task import FixedTask
from src.core.task import Task
from src.core.model import reset_model
from src.core.result import Result
from src.core.server import Server
from src.optimal.fixed_optimal import fixed_optimal_algorithm


def fixed_vcg_auction(jobs: List[FixedTask], servers: List[Server], time_limit: int,
                      debug_running: bool = False, debug_results: bool = False) -> Optional[Result]:
    """
    Combinatorial Double auction solved through VCG auction algorithm

    :param jobs: a list of jobs
    :param servers: a list of servers
    :param time_limit:The time limit
    :param debug_running: debug the running
    :param debug_results: debug the results
    :return: the results
    """
    start_time = time()

    # Price information
    job_prices: Dict[Task, float] = {}

    # Find the optimal solution
    if debug_running:
        print("Finding optimal")
    optimal_solution = fixed_optimal_algorithm(jobs, servers, time_limit=time_limit)
    if optimal_solution is None:
        return None
    elif debug_results:
        print("Optimal total utility: {}".format(optimal_solution))

    # Save the job and server information from the optimal solution
    allocated_jobs = [job for job in jobs if job.running_server]
    job_allocation: Dict[Task, Server] = {job: job.running_server for job in jobs}

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
        optimal_prime = fixed_optimal_algorithm(jobs_prime, servers, time_limit=time_limit)
        if optimal_prime is None:
            return None
        else:
            job_prices[job] = optimal_solution.sum_value - optimal_prime.sum_value
            if debug_results:
                print("Task {}: £{:.1f}, Value: {} ".format(job.name, job_prices[job], job.value))

    # Resets all of the jobs and servers and allocates all of their info from the original optimal solution
    reset_model(jobs, servers)
    for job in allocated_jobs:
        allocate(job, -1, -1, -1, job_allocation[job], job_prices[job])

    return Result('vcg', jobs, servers, time() - start_time, individual_compute_time=time_limit, show_money=True)
