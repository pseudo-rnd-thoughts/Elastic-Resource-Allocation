"""
All of the other evaluation scripts test the algorithm within a static / one-shot case, this script tests the greedy
    algorithms using batched time steps compared to an optimal fixed speed online case
"""

from __future__ import annotations

import json
import pprint
from typing import Iterable

from extra.online import online_batch_solver, minimal_flexible_optimal_solver, generate_batch_tasks
from src.core.core import reset_model
from src.core.fixed_task import generate_fixed_tasks
from src.extra.io import results_filename, parse_args
from src.extra.model import ModelDist, get_model
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import SumPowPercentage
from src.greedy.server_selection_policy import ProductResources
from src.greedy.task_prioritisation import UtilityDeadlinePerResource, ResourceSqrt
from src.optimal.fixed_optimal import fixed_optimal_solver


def batch_evaluation(model_dist: ModelDist, repeat_num: int, repeats: int = 20,
                     batch_lengths: Iterable[int] = (1, 5, 10, 30), time_steps: int = 1000,
                     mean_arrival_rate: int = 0.5, std_arrival_rate: float = 0.5,
                     task_priority=UtilityDeadlinePerResource(ResourceSqrt()),
                     server_selection_policy=ProductResources(), resource_allocation_policy=SumPowPercentage()):
    """
    Evaluates the batch online

    :param model_dist: The model distribution
    :param repeat_num: The repeat number
    :param repeats: The number of repeats
    :param batch_lengths: List of batch lengths
    :param time_steps: Total number of time steps
    :param mean_arrival_rate: Mean arrival rate of tasks
    :param std_arrival_rate: Standard deviation arrival rate of tasks
    :param task_priority: The task prioritisation function
    :param server_selection_policy: Server selection policy
    :param resource_allocation_policy: Resource allocation policy
    """
    print(f'Evaluates difference in performance between batch and online algorithm for {model_dist.name} model with '
          f'{model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    model_results = []
    pp = pprint.PrettyPrinter()
    filename = results_filename('batch_online', model_dist, repeat_num)

    name = f'Greedy {task_priority.name}, {server_selection_policy.name}, ' \
           f'{resource_allocation_policy.name}'

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        # Generate the tasks and servers
        tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
        batch_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}
        pp.pprint(batch_results)

        # Batch greedy algorithm
        for batch_length in batch_lengths:
            batched_tasks = generate_batch_tasks(tasks, batch_length, time_steps)

            # Generate fixed tasks
            fixed_tasks = generate_fixed_tasks(tasks)
            batched_fixed_tasks = generate_batch_tasks(fixed_tasks, batch_length, time_steps)

            # Generate the foreknowledge fixed tasks
            foreknowledge_tasks = generate_fixed_tasks(tasks)
            batched_foreknowledge_tasks = generate_batch_tasks(foreknowledge_tasks, batch_length, time_steps)

            # Flatten the tasks
            flattened_tasks = [task for tasks in batched_tasks for task in tasks]
            flattened_fixed_tasks = [fixed_task for fixed_tasks in batched_fixed_tasks for fixed_task in fixed_tasks]
            flattened_foreknowledge_fixed_tasks = [t for ts in batched_foreknowledge_tasks for t in ts]

            algorithm_results = {}
            if batch_length <= 10:
                optimal_result = online_batch_solver(batched_tasks, servers, batch_length, 'Flexible Optimal',
                                                     minimal_flexible_optimal_solver, solver_time_limit=None)
                algorithm_results[optimal_result.algorithm] = optimal_result.store()
                optimal_result.pretty_print()
                reset_model(flattened_tasks, servers)

                fixed_optimal_result = online_batch_solver(batched_fixed_tasks, servers, batch_length, 'Fixed Optimal',
                                                           fixed_optimal_solver, time_limit=None)
                algorithm_results[fixed_optimal_result.algorithm] = fixed_optimal_result.store()
                fixed_optimal_result.pretty_print()
                reset_model(flattened_fixed_tasks, servers)

                foreknowledge_optimal_result = online_batch_solver(batched_foreknowledge_tasks, servers, batch_length,
                                                                   'Foreknowledge Fixed Optimal',
                                                                   fixed_optimal_solver, time_limit=None)
                algorithm_results[foreknowledge_optimal_result.algorithm] = foreknowledge_optimal_result.store()
                foreknowledge_optimal_result.pretty_print()
                reset_model(flattened_foreknowledge_fixed_tasks, servers)

            # Loop over all of the greedy policies permutations
            greedy_result = online_batch_solver(batched_tasks, servers, batch_length, name,
                                                greedy_algorithm, task_priority=task_priority,
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

    batch_evaluation(get_model(args.model, args.tasks, args.servers), args.repeat)
