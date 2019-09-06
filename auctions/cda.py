"""Combinatorial Double Auction"""

from __future__ import annotations
from typing import List, Dict, Optional
from math import exp

from core.job import Job
from core.server import Server
from core.result import Result
from core.model import reset_model

from docplex.cp.model import CpoModel
from docplex.cp.solution import SOLVE_STATUS_UNKNOWN


class FixedJob(Job):
    """Job with a fixing resource usage speed"""

    def __init__(self, job, servers):
        super().__init__("fixed " + job.name, job.required_storage, job.required_computation, job.required_results_data,
                         job.value, job.deadline)
        self.original_job = job
        self.loading_speed, self.compute_speed, self.sending_speed = min(
            ((s, w, r)
             for s in range(1, max(server.max_bandwidth for server in servers))
             for w in range(1, max(server.max_computation for server in servers))
             for r in range(1, max(server.max_bandwidth for server in servers))
             if job.required_storage * w * r + s * job.required_computation * r +
             s * w * job.required_results_data <= job.deadline * s * w * r),
            key=lambda x: exp(x[0]) ** 3 + exp(x[1]) ** 3 + exp(x[2]) ** 3)

    def reset_allocation(self):
        """
        Overrides the reset_allocation function from job to just change the server not resource speeds
        """
        self.running_server = None


def optimal_algorithm(jobs: List[FixedJob], servers: List[Server], time_limit) -> Optional[Result]:
    """
    Finds the optimal solution
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param time_limit:
    :return:
    """
    model = CpoModel("CDA")

    allocations = {(job, server): model.binary_var(name='{} job {} server'.format(job.name, server.name))
                   for job in jobs for server in servers}

    for server in servers:
        model.add(sum(job.required_storage * allocations[(job, server)] for job in jobs) <= server.max_storage)
        model.add(sum(job.compute_speed * allocations[(job, server)] for job in jobs) <= server.max_storage)
        model.add(sum((job.loading_speed + job.sending_speed) * allocations[(job, server)]
                      for job in jobs) <= server.max_storage)

    model.maximize(sum(job.value * allocations[(job, server)] for job in jobs for server in servers))

    model_solution = model.solve(TimeLimit=time_limit)
    if model_solution.get_solve_status() == SOLVE_STATUS_UNKNOWN:
        return None

    for job in jobs:
        for server in servers:
            if model_solution.get_value(allocations[(job, server)]):
                job.running_server = server
                server.allocate_job(job)

    return Result("CDA", jobs, servers)


def combinatorial_double_auction(jobs: List[Job], servers: List[Server], time: int = 60, debug_running: bool = False,
                                 debug_results: bool = False) -> Optional[Result]:
    """
    Combinatorial Double auction solved through VCG
    :param jobs: a list of jobs
    :param servers: a list of servers
    :param time:The time limit
    :param debug_running: debug the running
    :param debug_results: debug the results
    :return: the results
    """
    fixed_jobs = [FixedJob(job, servers) for job in jobs]

    if debug_running:
        print("Finding optimal")
    optimal_solution = optimal_algorithm(fixed_jobs, servers, time_limit=time)
    if optimal_solution is None:
        return None
    if debug_results:
        print("Optimal total utility: {}".format(optimal_solution.sum_value))

    job_prices: Dict[Job, float] = {}
    server_prices: Dict[Server, float] = {}
    allocated_jobs = [job for job in fixed_jobs if job.running_server]
    job_info: Dict[Job, Server] = {job: job.running_server for job in fixed_jobs}

    if debug_running:
        print("Allocated jobs: {}".format(", ".join([job.name for job in allocated_jobs])))

    for job in allocated_jobs:
        reset_model(fixed_jobs, servers)

        jobs_prime = fixed_jobs.copy()
        jobs_prime.remove(job)

        if debug_running:
            print("Solving for without job {}".format(job.name))
        optimal_prime = optimal_algorithm(jobs_prime, servers, time_limit=time)
        if optimal_prime is None:
            return None
        job_cost = (optimal_solution.sum_value - job.value) - optimal_prime.sum_value
        if debug_results:
            print("Job {}: £{:.1f}, Utility: {} ".format(job.name, job_cost, job.value))
        job_prices[job] = -job_cost

    for server in servers:
        reset_model(fixed_jobs, servers)

        servers_prime = servers.copy()
        servers_prime.remove(server)

        if debug_running:
            print("Solving for without server {}".format(server.name))
        optimal_prime = optimal_algorithm(fixed_jobs, servers_prime, time_limit=time)
        if optimal_prime is None:
            return None
        server_transfer = optimal_solution.sum_value - optimal_prime.sum_value
        if debug_results:
            print("Server {}: £{:.1f}".format(server.name, server_transfer))
        server_prices[server] = server_transfer

    reset_model(fixed_jobs, servers)
    for job in allocated_jobs:
        job.running_server = job_info[job]
        job.price = job_prices[job]
        job_info[job].allocate_job(job)

    return Result('vcg', fixed_jobs, servers)
