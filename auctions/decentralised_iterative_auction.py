"""Custom auctions by Mark and Seb"""

from __future__ import annotations

from math import inf
from random import choice
from time import time
from typing import List, Dict, Callable

from docplex.cp.model import CpoModel
from docplex.cp.solution import SOLVE_STATUS_UNKNOWN

from core.core import allocate
from core.job import Job
from core.result import Result
from core.server import Server


def assert_solution(loading_speeds: Dict[Job, int], compute_speeds: Dict[Job, int], sending_speeds: Dict[Job, int],
                    allocations: Dict[Job, bool]):
    """
    Assert that the solution is valid
    :param loading_speeds: The loading speeds
    :param compute_speeds: The compute speeds
    :param sending_speeds: The sending speeds
    :param allocations: The allocation of jobs
    """
    for job, allocation in allocations.items():
        if allocation:
            assert (job.required_storage * compute_speeds[job] * sending_speeds[job]) + \
                   (loading_speeds[job] * job.required_computation * sending_speeds[job]) + \
                   (loading_speeds[job] * compute_speeds[job] * job.required_results_data) <= \
                   (job.deadline * loading_speeds[job] * compute_speeds[job] * sending_speeds[job])


def evaluate_job_price(new_job: Job, server: Server, time_limit: int, initial_cost: int, debug_results: bool = False):
    """
    Evaluates the job price to run on server using a vcg mechanism
    :param new_job: A new job
    :param server: A server
    :param time_limit: The solve time limit
    :param initial_cost: The initial cost of the job
    :param debug_results: Prints the result from the model solution
    :return: The results from the job prices
    """
    assert time_limit > 0, "Time limit: {}".format(time_limit)

    if debug_results:
        print("Evaluating job {}'s price on server {}".format(new_job.name, server.name))
    model = CpoModel("Job {} Price".format(new_job.name))

    # Add the new job to the list of server allocated jobs
    jobs = server.allocated_jobs + [new_job]

    # Create all of the resource speeds variables
    loading_speed = {job: model.integer_var(min=1, max=server.max_bandwidth-1,
                                            name="Job {} loading speed".format(job.name)) for job in jobs}
    compute_speed = {job: model.integer_var(min=1, max=server.max_computation,
                                            name="Job {} compute speed".format(job.name)) for job in jobs}
    sending_speed = {job: model.integer_var(min=1, max=server.max_bandwidth-1,
                                            name="Job {} sending speed".format(job.name)) for job in jobs}
    # Create all of the allocation variables however only on the currently allocated jobs
    allocation = {job: model.binary_var(name="Job {} allocated".format(job.name)) for job in server.allocated_jobs}

    # Add the deadline constraint
    for job in jobs:
        model.add((job.required_storage / loading_speed[job]) +
                  (job.required_computation / compute_speed[job]) +
                  (job.required_results_data / sending_speed[job]) <= job.deadline)

    # Add the server resource constraints
    model.add(sum(job.required_storage * allocated for job, allocated in allocation.items()) +
              new_job.required_storage <= server.max_storage)
    model.add(sum(compute_speed[job] * allocated for job, allocated in allocation.items()) +
              compute_speed[new_job] <= server.max_computation)
    model.add(sum((loading_speed[job] + sending_speed[job]) * allocated for job, allocated in allocation.items()) +
              (loading_speed[new_job] + sending_speed[new_job]) <= server.max_bandwidth)

    # The optimisation function
    model.maximize(sum(job.price * allocated for job, allocated in allocation.items()))

    # Solve the model with a time limit
    model_solution = model.solve(log_output=None, RelativeOptimalityTolerance=0.01, TimeLimit=time_limit)

    # If the model solution failed then return an infinite price
    if model_solution.get_solve_status() == SOLVE_STATUS_UNKNOWN:
        print("Decentralised model failure")
        return inf, {}, {}, {}, {}, server, jobs

    # Get the max server profit that the model finds
    max_server_profit = model_solution.get_objective_values()[0]

    # Calculate the job price through a vcg similar function
    job_price = server.revenue - max_server_profit + server.price_change
    if job_price < initial_cost:  # Add an initial cost the job if the price is less than a set price
        job_price = initial_cost

    # Get the resource speeds and job allocations
    loading = {job: model_solution.get_value(loading_speed[job]) for job in jobs}
    compute = {job: model_solution.get_value(compute_speed[job]) for job in jobs}
    sending = {job: model_solution.get_value(sending_speed[job]) for job in jobs}
    allocation = {job: model_solution.get_value(allocated) for job, allocated in allocation.items()}

    # Check that the solution is valid
    assert_solution(loading, compute, sending, allocation)

    if debug_results:
        print("Sever: {} - Max server profit: {}, prior server total price: {} therefore job price: {}"
              .format(server.name, model_solution.get_objective_values()[0], server.revenue, job_price))

    return job_price, loading, compute, sending, allocation, server


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
    :return: The number of messages to allocate the job
    """
    server.reset_allocations()

    # Allocate the new job to the server
    allocate(new_job, loading[new_job], compute[new_job], sending[new_job], server, job_price)
    messages = 1

    # For each of the job, if the job is allocated then allocate the job or reset the job
    for job, allocated in allocation.items():
        if allocated:
            allocate(job, loading[job], compute[job], sending[job], server, job.price)
        else:
            job.reset_allocation()
            unallocated_jobs.append(job)
            messages += 1

        if debug_allocations:
            print("Job {} is {} to server {} with loading {}, compute {} and sending {}"
                  .format(job.name, "allocated" if allocation[job] else "unallocated", server.name,
                          loading[job], compute[job], sending[job]))
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
    start_time: float = time()

    # Checks that all of the server price change are greater than zero
    assert all(server.price_change > 0 for server in servers), \
        "Price change - " + ', '.join(["{}: {}".format(server.name, server.price_change) for server in servers])

    # Calculate the initial job cost for each job
    initial_job_cost = {job: initial_cost(job) if initial_cost is not None else -1 for job in jobs}
    unallocated_jobs = jobs.copy()

    iterations: int = 0
    messages: int = 0

    # While there are unallocated job then loop
    while len(unallocated_jobs):
        # Choice a random job from the list
        job: Job = choice(unallocated_jobs)

        # Calculate the min job price from all of the servers
        job_price, loading, compute, sending, allocation, server = \
            min((evaluate_job_price(job, server, time_limit, initial_job_cost[job]) for server in servers),
                key=lambda bid: bid[0])
        messages += 2 * len(servers)

        assert_solution(loading, compute, sending, allocation)

        # If the job price is less than the job value then allocate the job else remove the
        if job_price <= job.value:
            if debug_allocation:
                print("Adding job {} to server {} with price {}".format(job.name, server.name, job_price))
            messages += allocate_jobs(job_price, job, server, loading, compute, sending, allocation, unallocated_jobs)
        elif debug_allocation:
            print("Removing Job {} from the unallocated job as the min price is {} and job value is {}"
                  .format(job.name, job_price, job.value))
        unallocated_jobs.remove(job)

        if debug_allocation:
            print("Number of unallocated jobs: {}".format(len(unallocated_jobs)))
        iterations += 1

    if debug_results:
        print("It is finished, number of iterations: {} with social welfare: {}"
              .format(iterations, sum(server.revenue for server in servers)))
        for server in servers:
            print("Server {}: total revenue - {}".format(server.name, server.revenue))
            print("\tJobs - {}".format(', '.join(["{}: £{}".format(job.name, job.price)
                                                  for job in server.allocated_jobs])))

    return Result("Iterative", jobs, servers, time() - start_time, individual_compute_time=time_limit, show_money=True,
                  total_iterations=iterations, total_messages=messages)
