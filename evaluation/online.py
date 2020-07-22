"""
All of the other evaluation scripts test the algorithm within a static / one-shot case, this script tests the greedy
    algorithms using batched time steps compared to an optimal fixed speed online case
"""

from __future__ import annotations

import json
import pprint
from math import floor
from time import time
from typing import Iterable, List

from core.core import reset_model
from core.fixed_task import FixedTask, SumSpeedPowsFixedPolicy
from core.server import Server
from core.task import Task
from extra.io import results_filename, parse_args
from extra.result import Result, resource_usage
from extra.visualise import minimise_resource_allocation
from greedy.greedy import greedy_algorithm
from optimal.fixed_optimal import fixed_optimal_solver
from optimal.flexible_optimal import flexible_optimal_solver
from src.extra.model import ModelDistribution
from src.greedy.resource_allocation_policy import policies as resource_allocation_policies
from src.greedy.server_selection_policy import policies as server_selection_policies
from src.greedy.value_density import policies as value_densities


def online_batch_solver(batched_tasks: List[List[Task]], servers: List[Server], batch_length: int,
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
                                      if current_time_step < task.auction_time + task.deadline]
            # Calculate how much of the batch, the task will be allocate for
            batch_percent = {task: 1 if next_time_step < task.auction_time + task.deadline else
                             ((task.auction_time + task.deadline - current_time_step) / batch_length)
                             for task in server.allocated_tasks}
            assert all(0 < percent <= 1 for percent in batch_percent.values()), list(batch_percent.values())

            # Update the server available resources
            server.available_storage = server.storage_capacity - \
                floor(sum(task.required_storage for task in server.allocated_tasks))
            assert 0 <= server.available_storage <= server.storage_capacity, server.available_storage

            server.available_computation = server.computation_capacity - \
                floor(sum(task.compute_speed * batch_percent[task] for task in server.allocated_tasks))
            assert 0 <= server.available_computation <= server.computation_capacity, server.available_computation

            server.available_bandwidth = server.bandwidth_capacity - \
                floor(sum((task.loading_speed + task.sending_speed) * batch_percent[task]
                          for task in server.allocated_tasks))
            assert 0 <= server.available_bandwidth <= server.bandwidth_capacity, server.available_bandwidth

    flatten_tasks = [task for tasks in batched_tasks for task in tasks]
    return Result(solver_name, flatten_tasks, servers, time() - start_time, limited=True, **{
        'server social welfare': {server.name: server_social_welfare[server] for server in servers},
        'server storage used': {server.name: server_storage_usage[server] for server in servers},
        'server computation used': {server.name: server_computation_usage[server] for server in servers},
        'server bandwidth used': {server.name: server_bandwidth_usage[server] for server in servers},
        'server num tasks allocated': {server.name: server_num_tasks_allocated[server] for server in servers}
    })


def generate_batch_tasks(tasks: List[Task], batch_length: int, time_steps: int) -> List[List[Task]]:
    """
    Generate batch tasks with updated task deadlines

    :param tasks: List of tasks
    :param batch_length: The batch length integer
    :param time_steps: Total number of time steps
    :return: List of batched tasks
    """
    return [
        [task.batch(time_step)
         for task in tasks if time_step <= task.auction_time < time_step + batch_length]
        for time_step in range(0, time_steps + time_steps % batch_length, batch_length)
    ]


def minimal_flexible_optimal_solver(tasks: List[Task], servers: List[Server],
                                    solver_time_limit: int = 3, minimise_time_limit: int = 2):
    """
    Minimise the resources used by flexible optimal solver

    :param tasks: List of tasks
    :param servers: List of servers
    :param solver_time_limit: Solver time limit
    :param minimise_time_limit: Minimise solver time limit
    """
    valid_servers = [server for server in servers
                     if 1 <= server.available_computation and 1 <= server.available_bandwidth]
    flexible_optimal_solver(tasks, valid_servers, solver_time_limit)
    minimise_resource_allocation(tasks, valid_servers, minimise_time_limit)


def batch_online_evaluation(model_dist: ModelDistribution, repeat_num: int, repeats: int = 10,
                            batch_lengths: Iterable[int] = (1, 2, 3, 4, 5), time_steps: int = 200,
                            mean_arrival_rate: int = 4, std_arrival_rate: float = 2,
                            optimal_time_limit: int = 3, fixed_optimal_time_limit: int = 5):
    """
    Evaluates the batch online

    :param model_dist: The model distribution
    :param repeat_num: The repeat number
    :param repeats: The number of repeats
    :param batch_lengths: List of batch lengths
    :param time_steps: Total number of time steps
    :param mean_arrival_rate: Mean arrival rate of tasks
    :param std_arrival_rate: Standard deviation arrival rate of tasks
    :param optimal_time_limit: Optimal time limit
    :param fixed_optimal_time_limit: Fixed optimal time limit
    """
    print(f'Evaluates difference in performance between batch and online algorithm for {model_dist.name} model with '
          f'{model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    model_results = []
    pp = pprint.PrettyPrinter()
    filename = results_filename('batch_online', model_dist, repeat_num)

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        # Generate the tasks and servers
        tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
        fixed_tasks = [FixedTask(task, SumSpeedPowsFixedPolicy()) for task in tasks]
        original_server_capacities = {server: (server.computation_capacity, server.bandwidth_capacity)
                                      for server in servers}
        batch_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}
        pp.pprint(batch_results)

        # Batch greedy algorithm
        for batch_length in batch_lengths:
            batched_tasks = generate_batch_tasks(tasks, batch_length, time_steps)
            fixed_batched_tasks = generate_batch_tasks(fixed_tasks, batch_length, time_steps)
            flattened_tasks = [task for tasks in batched_tasks for task in tasks]

            # Update the server capacities
            for server in servers:
                server.computation_capacity = original_server_capacities[server][0] * batch_length
                server.bandwidth_capacity = original_server_capacities[server][1] * batch_length

            algorithm_results = {}

            # Online fixed optimal
            fixed_optimal_result = online_batch_solver(fixed_batched_tasks, servers, batch_length, 'Fixed Optimal',
                                                       fixed_optimal_solver, time_limit=fixed_optimal_time_limit)
            algorithm_results[fixed_optimal_result.algorithm] = fixed_optimal_result.store()
            fixed_optimal_result.pretty_print()
            reset_model([], servers)

            # Online flexible optimal
            optimal_result = online_batch_solver(batched_tasks, servers, batch_length, 'Flexible Optimal',
                                                 minimal_flexible_optimal_solver, solver_time_limit=optimal_time_limit)
            algorithm_results[optimal_result.algorithm] = optimal_result.store()
            optimal_result.pretty_print()
            reset_model(flattened_tasks, servers)

            # Loop over all of the greedy policies permutations
            for value_density in value_densities:
                for server_selection_policy in server_selection_policies:
                    for resource_allocation_policy in resource_allocation_policies:
                        name = f'Greedy {value_density.name}, {server_selection_policy.name}, ' \
                               f'{resource_allocation_policy.name}'
                        greedy_result = online_batch_solver(batched_tasks, servers, batch_length, name,
                                                            greedy_algorithm, value_density=value_density,
                                                            server_selection_policy=server_selection_policy,
                                                            resource_allocation_policy=resource_allocation_policy)
                        algorithm_results[greedy_result.algorithm] = greedy_result.store()
                        greedy_result.pretty_print()
                        reset_model(flattened_tasks, servers)

            # Add the results to the data
            batch_results[f'batch length {batch_length}'] = algorithm_results
        model_results.append(batch_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


if __name__ == "__main__":
    args = parse_args()

    if args.extra == '' or args.extra == 'mean4':
        batch_online_evaluation(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
    elif args.extra == 'mean7':
        batch_online_evaluation(ModelDistribution(args.file, args.tasks, args.servers), args.repeat,
                                mean_arrival_rate=7)
    else:
        raise Exception(f'Unknown extra argument: {args.extra}')
