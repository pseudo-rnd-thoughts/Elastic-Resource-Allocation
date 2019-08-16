"""Implementation of an VCG auction"""

from __future__ import annotations
from typing import List, Dict, Tuple

from core.job import Job
from core.server import Server
from core.model import reset_model
from optimal.optimal import optimal_algorithm


def vcg_auction(jobs: List[Job], servers: List[Server], debug: bool = False, debug_time: bool = False):
    """
    Implementation of a VCG auction
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param debug: Debug what is being calculated
    :param debug_time: Debug how long the allocation took to calculate
    """
    if debug:
        print("Finding optimal")
    optimal_solution = optimal_algorithm(jobs, servers, debug_time=True)
    print("Optimal total utility: {}".format(optimal_solution.total_utility))

    allocated_jobs = [job for job in jobs if job.running_server]
    job_prices: Dict[Job, float] = {}
    server_prices: Dict[Server, float] = {}
    job_info: Dict[Job, Tuple[int, int, int, Server]] = {
        job: (job.loading_speed, job.compute_speed, job.sending_speed, job.running_server) for job in allocated_jobs
    }

    if debug:
        print("Allocated jobs: {}".format(", ".join([job.name for job in allocated_jobs])))

    for job in allocated_jobs:
        reset_model(jobs, servers)

        jobs_prime = jobs.copy()
        jobs_prime.remove(job)

        if debug:
            print("Solving for without job {}".format(job.name))
        optimal_prime = optimal_algorithm(jobs_prime, servers, debug_time=debug_time)
        job_cost = optimal_solution.total_utility - optimal_prime.total_utility
        print("Job {}: £{:.1f}, Utility: {} ".format(job.name, job_cost, job.utility))
        job_prices[job] = job_cost

    for server in servers:
        reset_model(jobs, servers)

        servers_prime = servers.copy()
        servers_prime.remove(server)

        if debug:
            print("Solving for without server {}".format(server.name))
        optimal_prime = optimal_algorithm(jobs, servers_prime, debug_time=debug_time)
        server_transfer = optimal_solution.total_utility - optimal_prime.total_utility
        print("Server {}: £{:.1f}".format(server.name, server_transfer))
        server_prices[server] = server_transfer

    reset_model(jobs, servers)
    for job in allocated_jobs:
        s, w, r, server = job_info[job]
        job.allocate(s, w, r, server, price=job_prices[job])
        server.allocate_job(job)

