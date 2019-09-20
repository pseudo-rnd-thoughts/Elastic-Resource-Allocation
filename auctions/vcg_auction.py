"""Implementation of an VCG auctions"""

from __future__ import annotations

from time import time
from typing import List, Dict, Tuple, Optional

from core.core import list_copy_remove
from core.job import Job
from core.model import reset_model
from core.result import Result
from core.server import Server
from optimal.optimal import optimal_algorithm


def vcg_auction(jobs: List[Job], servers: List[Server], time_limit: int,
                debug_running: bool = False, debug_results: bool = False) -> Optional[Result]:
    """
    Implementation of a VCG auctions
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param time_limit: The time to run the optimal for
    :param debug_running: Debug what is being calculated
    :param debug_results: Debug the results for each job and server
    """
    start_time = time()

    # Price information
    job_prices: Dict[Job, float] = {}
    server_revenues: Dict[Server, float] = {}

    # Find the optimal solution
    if debug_running:
        print("Finding optimal")
    optimal_solution = optimal_algorithm(jobs, servers, time_limit=time_limit)
    if optimal_solution is None:
        return None
    elif debug_results:
        print("Optimal total utility: {}".format(optimal_solution.sum_value))

    # Save the job and server information from the optimal solution
    allocated_jobs = [job for job in jobs if job.running_server]
    job_info: Dict[Job, Tuple[int, int, int, Server]] = {
        job: (job.loading_speed, job.compute_speed, job.sending_speed, job.running_server) for job in jobs
    }

    if debug_running:
        print("Allocated jobs: {}".format(", ".join([job.name for job in allocated_jobs])))

    # For each allocated job, find the sum of values if the job doesnt exist
    for job in allocated_jobs:
        # Reset the model and remove the job from the job list
        reset_model(jobs, servers)
        jobs_prime = list_copy_remove(jobs, job)

        # Find the optimal solution where the job doesnt exist
        if debug_running:
            print("Solving for without job {}".format(job.name))
        optimal_prime = optimal_algorithm(jobs_prime, servers, time_limit=time_limit)
        if optimal_prime is None:
            return None
        else:
            job_prices[job] = (optimal_solution.sum_value - job.value) - optimal_prime.sum_value
            if debug_results:
                print("Job {}: £{:.1f}, Value: {} ".format(job.name, job_prices[job], job.value))

    # For each server. find the sum of values if the server doesnt exist
    for server in servers:
        # Reset the model and removes the server from the server list
        reset_model(jobs, servers)
        servers_prime = list_copy_remove(servers, server)

        # Find the optimal solution where the server doesnt exist
        if debug_running:
            print("Solving for without server {}".format(server.name))
        optimal_prime = optimal_algorithm(jobs, servers_prime, time_limit=time_limit)
        if optimal_prime is None:
            return None
        else:
            server_revenues[server] = optimal_solution.sum_value - optimal_prime.sum_value
            if debug_results:
                print("Server {}: £{:.1f}".format(server.name, server_revenues[server]))

    # Reset the model and allocates all of the their info from the original optimal solution
    reset_model(jobs, servers)
    for job in allocated_jobs:
        s, w, r, server = job_info[job]
        job.allocate(s, w, r, server, price=job_prices[job])
        server.allocate_job(job)

    # Check that the job prices sum to the same value as the server revenues,
    # else the optimal solution hasn't been found at some point
    if sum(job_prices.values()) != sum(server_revenues.values()):
        print("VCG fail as sum of job prices {} != sum of server prices {}"
              .format(sum(job_prices.values()), sum(server_revenues.values())))

    return Result('vcg', jobs, servers, time() - start_time, individual_compute_time=time_limit, show_money=True,
                  failure=sum(job_prices.values()) != sum(server_revenues.values()))
