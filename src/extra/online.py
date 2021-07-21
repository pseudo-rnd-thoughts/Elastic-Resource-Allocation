"""
For online resource allocation using any resource allocation mechanism (optimal, greedy, fixed, etc)
"""

import sys
from math import ceil
from time import time
from typing import List

from src.core.server import Server
from src.core.elastic_task import ElasticTask
from src.extra.result import Result, resource_usage
from src.extra.visualise import minimal_allocated_resources_solver
from src.optimal.elastic_optimal import elastic_optimal_solver


def online_batch_solver(batched_tasks: List[List[ElasticTask]], servers: List[Server], batch_length: int,
                        solver_name: str, solver, **solver_args) -> Result:
    """
    Generic online batch solver

    :param batched_tasks: List of batch tasks
    :param servers: List of servers
    :param batch_length: Batch length
    :param solver_name: Solver name
    :param solver: Solver function
    :param solver_args: Solver function arguments
    :return: Online results
    """
    start_time = time()
    server_social_welfare = {server: 0 for server in servers}
    server_storage_usage = {server: [] for server in servers}
    server_computation_usage = {server: [] for server in servers}
    server_bandwidth_usage = {server: [] for server in servers}
    server_num_tasks_allocated = {server: [] for server in servers}

    for batch_num, batch_tasks in enumerate(batched_tasks):
        solver(batch_tasks, servers, **solver_args)

        for server in servers:
            # Save the current information for the server
            server_social_welfare[server] += sum(task.value for task in batch_tasks if task.running_server is server)
            server_storage_usage[server].append(resource_usage(server, 'storage'))
            server_computation_usage[server].append(resource_usage(server, 'computation'))
            server_bandwidth_usage[server].append(resource_usage(server, 'bandwidth'))
            server_num_tasks_allocated[server].append(len(server.allocated_tasks))

            # Get the current batch time step and the next batch time step
            current_time_step, next_time_step = batch_length * batch_num, batch_length * (batch_num + 1)

            # Update the server allocation task to only tasks within the next batch step time
            server.allocated_tasks = [task for task in server.allocated_tasks
                                      if next_time_step <= task.auction_time + task.deadline]
            # Calculate how much of the batch, the task will be allocate for
            # batch_multiplier = {task: batch_length if next_time_step <= task.auction_time + task.deadline else
            #                  (task.auction_time + task.deadline - next_time_step) for task in server.allocated_tasks}
            # assert all(0 < multiplier <= batch_length for multiplier in batch_multiplier.values()), \
            #     list(batch_multiplier.values())

            # Update the server available resources
            server.available_storage = server.storage_capacity - \
                sum(task.required_storage for task in server.allocated_tasks)
            assert 0 <= server.available_storage <= server.storage_capacity, server.available_storage

            server.available_computation = server.computation_capacity - \
                ceil(sum(task.compute_speed for task in server.allocated_tasks))
            assert 0 <= server.available_computation <= server.computation_capacity, server.available_computation

            server.available_bandwidth = server.bandwidth_capacity - \
                ceil(sum((task.loading_speed + task.sending_speed) for task in server.allocated_tasks))
            assert 0 <= server.available_bandwidth <= server.bandwidth_capacity, server.available_bandwidth

    flatten_tasks = [task for tasks in batched_tasks for task in tasks]
    return Result(solver_name, flatten_tasks, servers, time() - start_time, limited=True, **{
        'server social welfare': {server.name: server_social_welfare[server] for server in servers},
        'server storage used': {server.name: server_storage_usage[server] for server in servers},
        'server computation used': {server.name: server_computation_usage[server] for server in servers},
        'server bandwidth used': {server.name: server_bandwidth_usage[server] for server in servers},
        'server num tasks allocated': {server.name: server_num_tasks_allocated[server] for server in servers}
    })


def generate_batch_tasks(tasks: List[ElasticTask], batch_length: int, time_steps: int) -> List[List[ElasticTask]]:
    """
    Generate batch tasks with updated task deadlines that has the first batch at batch_length, the second at
        batch_length * 2, ..., to time_steps

    :param tasks: List of tasks
    :param batch_length: The batch length integer
    :param time_steps: Total number of time steps
    :return: List of batched tasks
    """
    return [
        [task.batch(time_step) for task in tasks if time_step - batch_length <= task.auction_time < time_step]
        for time_step in range(batch_length, time_steps + time_steps % batch_length + 1, batch_length)
    ]


def minimal_resources_elastic_optimal_solver(tasks: List[ElasticTask], servers: List[Server],
                                             solver_time_limit: int = 3, minimise_time_limit: int = 2):
    """
    Minimise the resources used by elastic optimal solver

    :param tasks: List of tasks
    :param servers: List of servers
    :param solver_time_limit: Solver time limit
    :param minimise_time_limit: Minimise solver time limit
    """
    valid_servers = [server for server in servers
                     if 1 <= server.available_computation and 1 <= server.available_bandwidth]
    model_solution = elastic_optimal_solver(tasks, valid_servers, solver_time_limit)
    if model_solution:
        # Find the minimum resource that could be allocation
        minimal_allocated_resources_solver(tasks, valid_servers, minimise_time_limit)
        return Result('Elastic Optimal', tasks, servers, round(model_solution.get_solve_time(), 2),
                      **{'solve status': model_solution.get_solve_status(),
                         'cplex objective': model_solution.get_objective_values()[0]})
    else:
        print(f'Elastic Optimal error', file=sys.stderr)
        return Result('Elastic Optimal', tasks, servers, 0, limited=True)
