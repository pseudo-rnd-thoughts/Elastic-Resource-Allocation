"""
All of the other evaluation scripts test the algorithm within a static / one-shot case, this script tests the greedy
    algorithms using batched time steps compared to an optimal fixed speed online case
"""

from __future__ import annotations

import json
import pprint
from random import gauss
from typing import Iterable, List, Tuple

from core.core import reset_model
from core.fixed_task import FixedTask, FixedSumSpeeds
from core.server import Server
from core.task import Task
from extra.io import results_filename
from extra.result import Result, resource_usage
from greedy.greedy import greedy_algorithm
from optimal.fixed_optimal import fixed_optimal
from optimal.flexible_optimal import flexible_optimal
from optimal.relaxed_flexible import relaxed_flexible
from src.extra.model import ModelDistribution
from src.greedy.resource_allocation_policy import policies as resource_allocation_policies
from src.greedy.server_selection_policy import policies as server_selection_policies
from src.greedy.value_density import policies as value_densities


def batch_solver(batched_tasks: List[List[Task]], servers: List[Server], batch_length: int, time_steps: int,
                 solver) -> Result:
    server_social_welfare = {server: 0 for server in servers}
    server_storage_usage = {server: [] for server in servers}
    server_computation_usage = {server: [] for server in servers}
    server_bandwidth_usage = {server: [] for server in servers}
    server_num_tasks_allocated = {server: [] for server in servers}

    for pos in range(len(batched_tasks)):
        solver(batched_tasks[pos], servers)

        for server in servers:
            server_social_welfare[server] += sum()
            server_storage_usage[server].append(resource_usage(server, 'storage'))
            server_computation_usage[server].append(resource_usage(server, 'computation'))
            server_bandwidth_usage[server].append(resource_usage(server, 'bandwidth'))
            server_num_tasks_allocated[server].append(len(server.allocated_tasks))

    return Result(limited=True, **{
        'server social welfare': {server.name: server_social_welfare[server] for server in servers},
        'server storage used': {server.name: server_storage_usage[server] for server in servers},
        'server computation used': {server.name: server_computation_usage[server] for server in servers},
        'server bandwidth used': {server.name: server_bandwidth_usage[server] for server in servers},
        'server num tasks allocated': {server.name: server_num_tasks_allocated[server] for server in servers}
    })


def batch_tasks(tasks: List[Task], batch_length: int, time_steps: int) -> List[List[Task]]:
    return [
        [task for task in tasks if time_step <= task.auction_time < time_step + batch_length]
        for time_step in range(0, time_steps, batch_length)
    ]


def generate_online_model_dist(model_dist: ModelDistribution, time_steps: int, task_arrival_rate_mean: int,
                               task_arrival_rate_std: float) -> Tuple[List[Task], List[Server]]:
    tasks, task_id = [], 0
    for time_step in range(time_steps):
        for _ in range(max(1, int(gauss(task_arrival_rate_mean, task_arrival_rate_std)))):
            task = model_dist.generate_rnd_task(task_id)
            task.auction_time, task_id = time_step, task_id + 1
            # task.deadline = time_step + task.deadline
            tasks.append(task)

    return tasks, model_dist.generate_servers()


def batch_online(model_dist: ModelDistribution, repeat_num: int, repeats: int = 10,
                 batch_lengths: Iterable[int] = (1, 5, 10, 15), time_steps: int = 200,
                 task_arrival_rate_mean: int = 1, task_arrival_rate_std: float = 0.4,
                 optimal_time_limit: int = 30, fixed_optimal_time_limit: int = 30, relaxed_time_limit: int = 30):
    print(f'Evaluates difference in performance between batch and online algorithm for {model_dist.name} model with '
          f'{model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    model_results = []
    pp = pprint.PrettyPrinter()
    filename = results_filename('batch_online', model_dist, repeat_num)

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        # Generate the tasks and servers
        tasks, servers = generate_online_model_dist(model_dist, time_steps,
                                                    task_arrival_rate_mean, task_arrival_rate_std)
        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]

        batch_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}
        pp.pprint(batch_results)

        original_capacities = {server: (server.computation_capacity, server.bandwidth_capacity) for server in servers}
        for batch_length in batch_lengths:
            # Update the server capacities
            algorithm_results = {}

            # Find the optimal solution
            optimal_result = flexible_optimal(tasks, servers, optimal_time_limit)
            algorithm_results[optimal_result.algorithm] = optimal_result.store()
            optimal_result.pretty_print()
            reset_model(tasks, servers)

            # Find the fixed solution
            fixed_optimal_result = fixed_optimal(fixed_tasks, servers, fixed_optimal_time_limit)
            algorithm_results[fixed_optimal_result.algorithm] = fixed_optimal_result.store()
            fixed_optimal_result.pretty_print()
            reset_model(fixed_tasks, servers)

            # Find the relaxed solution
            relaxed_result = relaxed_flexible(tasks, servers, relaxed_time_limit)
            algorithm_results[relaxed_result.algorithm] = relaxed_result.store()
            relaxed_result.pretty_print()
            reset_model(tasks, servers)

            # Loop over all of the greedy policies permutations
            for value_density in value_densities:
                for server_selection_policy in server_selection_policies:
                    for resource_allocation_policy in resource_allocation_policies:
                        greedy_result = greedy_algorithm(tasks, servers, value_density, server_selection_policy,
                                                         resource_allocation_policy)
                        algorithm_results[greedy_result.algorithm] = greedy_result.store()
                        greedy_result.pretty_print()
                        reset_model(tasks, servers)

            # Add the results to the data
            batch_results[f'{batch_length} length'] = algorithm_results
        model_results.append(batch_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')
