"""Implementation of an VCG auction"""

from __future__ import annotations
from typing import List

from core.job import Job
from core.server import Server
from core.model import reset_model
from optimal.optimal import optimal_algorithm


def vcg_auction(jobs: List[Job], servers: List[Server]):
    """
    Implementation of a VCG auction
    :param jobs: A list of jobs
    :param servers: A list of servers
    """

    optimal_solution = optimal_algorithm(jobs, servers)
    print("Total optimal: {}".format(optimal_solution.total_utility))
    allocated_jobs = (job for job in jobs if job.running_server)

    for job in allocated_jobs:
        jobs_prime = jobs.copy()
        jobs_prime.remove(job)

        optimal_prime = optimal_algorithm(jobs_prime, servers)
        job_cost = (optimal_solution.total_utility - job.utility) - optimal_prime.total_utility
        reset_model(jobs, servers)

        print("Job {}: £{:.1f}".format(job.name, job_cost))

    for server in servers:
        servers_prime = servers.copy()
        servers_prime.remove(server)

        optimal_prime = optimal_algorithm(jobs, servers_prime)
        server_transfer = optimal_solution.total_utility - optimal_prime.total_utility
        reset_model(jobs, servers)

        print("Server {}: £{:.1f}".format(server.name, server_transfer))
