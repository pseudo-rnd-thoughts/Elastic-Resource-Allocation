"""Custom auctions by Mark and Seb"""

from __future__ import annotations

from random import choice
from typing import List, Dict, Callable
from math import inf
from time import time

from core.job import Job
from core.server import Server
from core.result import Result

from docplex.cp.model import CpoModel
from docplex.cp.solution import SOLVE_STATUS_UNKNOWN


def evaluate_job_price(new_job: Job, server: Server, initial_cost: int, time_limit: int, debug_results: bool = False):
    """
    Evaluates the job price to run on server using a vcg mechanism
    :param new_job: A new job
    :param server: A server
    :param initial_cost: The initial cost of the job
    :param time_limit: The solve time limit
    :param debug_results: Prints the result from the model solution
    :return: The results from the job prices
    """
    if debug_results:
        print("Evaluating job {}'s price on server {}".format(new_job.name, server.name))
    model = CpoModel("Job Price")

    jobs = server.allocated_jobs + [new_job]
    loading_speed = {job: model.integer_var(min=1, max=server.max_bandwidth,
                                            name="Job {} loading speed".format(job.name)) for job in jobs}
    compute_speed = {job: model.integer_var(min=1, max=server.max_computation,
                                            name="Job {} compute speed".format(job.name)) for job in jobs}
    sending_speed = {job: model.integer_var(min=1, max=server.max_bandwidth,
                                            name="Job {} sending speed".format(job.name)) for job in jobs}
    allocation = {job: model.binary_var(name="Job {} allocated".format(job.name)) for job in server.allocated_jobs}

    for job in jobs:
        model.add(job.required_storage / loading_speed[job] +
                  job.required_computation / compute_speed[job] +
                  job.required_results_data / sending_speed[job] <= job.deadline)

    model.add(sum(job.required_storage * allocated for job, allocated in allocation.items()) +
              new_job.required_storage <= server.max_storage)
    model.add(sum(compute_speed[job] * allocated for job, allocated in allocation.items()) +
              compute_speed[new_job] <= server.max_computation)
    model.add(sum((loading_speed[job] + sending_speed[job]) * allocated for job, allocated in allocation.items()) +
              (loading_speed[new_job] + sending_speed[new_job]) <= server.max_bandwidth)

    model.maximize(sum(job.price * allocated for job, allocated in allocation.items()))

    model_solution = model.solve(TimeLimit=time_limit)
    if model_solution.get_solve_status() == SOLVE_STATUS_UNKNOWN or model_solution.get_objective_values() is None:
        print("Decentralised model failure")
        return inf, {}, {}, {}, {}, server, jobs

    max_server_profit = model_solution.get_objective_values()[0]

    job_price = server.revenue - max_server_profit + server.price_change
    if job_price < initial_cost:
        job_price = initial_cost

    loading = {job: model_solution.get_value(loading_speed[job]) for job in jobs}
    compute = {job: model_solution.get_value(compute_speed[job]) for job in jobs}
    sending = {job: model_solution.get_value(sending_speed[job]) for job in jobs}
    allocation = {job: model_solution.get_value(allocated) for job, allocated in allocation.items()}

    if debug_results:
        print("Sever: {} - Max server profit: {}, prior server total price: {} therefore job price: {}"
              .format(server.name, model_solution.get_objective_values()[0], server.revenue, job_price))

    return job_price, loading, compute, sending, allocation, server, jobs


def allocate_jobs(job_price: float, new_job: Job, server: Server,
                  loading: Dict[Job, int], compute: Dict[Job, int], sending: Dict[Job, int],
                  allocation: Dict[Job, bool], unallocated_jobs: List[Job],
                  debug_allocations: bool = False, debug_result: bool = False) -> int:
    """
    Allocates a job to a server based on the last allocation
    :param job_price: The new job price
    :param new_job: The new job
    :param server: The server the job is allocated to
    :param loading: A dictionary of loading speeds of jobs
    :param compute: A dictionary of compute speeds of jobs
    :param sending: A dictionary of sending speeds of jobs
    :param allocation: A dictionary of if a job is allocated to server
    :param unallocated_jobs: A list of all unallocated jobs
    :param debug_allocations: Debug the allocations
    :param debug_result: Debug results
    :return: The number of messages
    """
    allocated_jobs = server.allocated_jobs
    server.reset_allocations()

    new_job.price = job_price
    new_job.allocate(loading[new_job], compute[new_job], sending[new_job], server, price=job_price)
    server.allocate_job(new_job)

    messages = 0

    for job in allocated_jobs:
        if allocation[job]:
            job.allocate(loading[job], compute[job], sending[job], server, job.price)
            server.allocate_job(job)

            if debug_allocations:
                print("Job {} is now allocated to server {}".format(job.name, allocation[job], server.name))
        else:
            job.reset_allocation()
            unallocated_jobs.append(job)
            messages += 1

            if debug_allocations:
                print("Job {} is unallocated to server {}".format(job.name, allocation[job], server.name))

    if debug_result:
        print("Server {}'s total price: {}".format(server.name, server.revenue))

    return messages


def decentralised_iterative_auction(jobs: List[Job], servers: List[Server], time_limit: int,
                                    initial_cost: Callable[[Job], int] = None,
                                    debug_allocation: bool = False, debug_results: bool = False) -> Result:
    """
    A iterative auctions created by Seb Stein and Mark Towers
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param initial_cost: An initial cost function
    :param time_limit: The solve time limit
    :param debug_allocation: Debug the allocation process
    :param debug_results: Debugs the results
    :return: A list of prices at each iteration
    """
    assert all(server.price_change > 0 for server in servers), \
        "Price change - " + ', '.join(["{}: {}".format(server.name, server.price_change) for server in servers])

    initial_job_cost = {job: initial_cost(job) if initial_cost is not None else -1 for job in jobs}

    unallocated_jobs = jobs.copy()

    iterations: int = 0
    messages: int = 0
    start_time: float = time()

    while len(unallocated_jobs):
        job: Job = choice(unallocated_jobs)

        job_price, loading, compute, sending, allocation, server, \
            jobs = min((evaluate_job_price(job, server, time_limit, initial_job_cost[job]) for server in servers),
                       key=lambda bid: bid[0])
        messages += 2 * len(servers)

        if job_price <= job.value:
            if debug_allocation:
                print("Adding job {} to server {} with price {}".format(job.name, server.name, job_price))
            messages += allocate_jobs(job_price, job, server, loading, compute, sending, allocation, unallocated_jobs)
            unallocated_jobs.remove(job)
        else:
            if debug_allocation:
                print("Removing Job {} from the unallocated job as the min price is {} and job value is {}"
                      .format(job.name, job_price, job.value))
            unallocated_jobs.remove(job)

        if debug_allocation:
            print("Number of unallocated jobs: {}, {}\n".format(len(unallocated_jobs), job in unallocated_jobs))

        # iteration_price.append(sum(server.revenue for server in servers))
        # iterative_value.append(sum(server.value for server in servers))
        iterations += 1

    if debug_results:
        print("It is finished, number of iterations: {} with social welfare: {}"
              .format(iterations, sum(server.revenue for server in servers)))
        for server in servers:
            print("Server {}: total revenue - {}".format(server.name, server.revenue))
            print("\tJobs - {}".format(', '.join(["{}: £{}".format(job.name, job.price)
                                                  for job in server.allocated_jobs])))

    total_time = time() - start_time
    return Result("Iterative", jobs, servers,
                  total_solve_time=total_time, total_iterations=iterations, total_messages=messages)
