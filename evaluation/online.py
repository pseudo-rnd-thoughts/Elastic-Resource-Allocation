"""
All of the other evaluation scripts test the algorithm within a static / one-shot case, this script tests the greedy
    algorithms using batched time steps compared to an optimal non-elastic speed online case
"""

from __future__ import annotations

import json

from src.core.core import reset_model
from src.core.non_elastic_task import generate_non_elastic_tasks
from src.extra.io import results_filename, parse_args
from src.extra.model import ModelDist, get_model
from src.extra.online import online_batch_solver, generate_batch_tasks
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation import SumPowPercentage
from src.greedy.server_selection import ProductResources, SumResources
from src.greedy.task_priority import UtilityDeadlinePerResourcePriority, ResourceSumPriority, ResourceProductPriority, \
    ValuePriority
from src.optimal.non_elastic_optimal import non_elastic_optimal_solver


def online_evaluation(model_dist: ModelDist, repeats: int = 20, time_steps: int = 200,
                      mean_arrival_rate: float = 1, std_arrival_rate: float = 2,
                      task_priority=UtilityDeadlinePerResourcePriority(ResourceSumPriority()),
                      server_selection=ProductResources(), resource_allocation=SumPowPercentage()):
    """
    Evaluates the batch online

    :param model_dist: The model distribution
    :param repeats: The number of repeats
    :param time_steps: Total number of time steps
    :param mean_arrival_rate: Mean arrival rate of tasks
    :param std_arrival_rate: Standard deviation arrival rate of tasks
    :param task_priority: The task prioritisation function
    :param server_selection: Server selection policy
    :param resource_allocation: Resource allocation policy
    """
    print(f'Evaluates difference in performance between batch and online algorithm for {model_dist.name} model with '
          f'{model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    print(f'Settings - Time steps: {time_steps}, mean arrival rate: {mean_arrival_rate} with std: {std_arrival_rate}')
    model_results = []

    filename = results_filename('online_resource_allocation', model_dist)
    greedy_name = f'Greedy {task_priority.name}, {server_selection.name}, {resource_allocation.name}'
    batch_length = 1

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        # Generate the tasks and servers
        tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
        algorithm_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}
        non_elastic_tasks = generate_non_elastic_tasks(tasks)

        valid_elastic_tasks = [task for task in tasks if batch_length < task.deadline]
        batched_elastic_tasks = generate_batch_tasks(valid_elastic_tasks, batch_length, time_steps)

        valid_non_elastic_tasks = [task for task in non_elastic_tasks if batch_length < task.deadline]
        batched_non_elastic_tasks = generate_batch_tasks(valid_non_elastic_tasks, batch_length, time_steps)

        # Flatten the tasks
        flattened_elastic_tasks = [task for tasks in batched_elastic_tasks for task in tasks]
        flattened_non_elastic_tasks = [task for tasks in batched_non_elastic_tasks for task in tasks]

        non_elastic_optimal_result = online_batch_solver(
            batched_non_elastic_tasks, servers, batch_length, 'Non-elastic Optimal', non_elastic_optimal_solver,
            time_limit=None)
        algorithm_results[non_elastic_optimal_result.algorithm] = non_elastic_optimal_result.store()
        reset_model(flattened_non_elastic_tasks, servers)

        # Loop over all of the greedy policies permutations
        greedy_result = online_batch_solver(
            batched_elastic_tasks, servers, batch_length, greedy_name, greedy_algorithm,
            task_priority=task_priority, server_selection=server_selection, resource_allocation=resource_allocation)
        algorithm_results[greedy_result.algorithm] = greedy_result.store()
        reset_model(flattened_elastic_tasks, servers)

        # Add the results to the data
        model_results.append(algorithm_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


def greedy_permutations(model_dist: ModelDist, repeats: int = 20, time_steps: int = 1000,
                        mean_arrival_rate: float = 2, std_arrival_rate: float = 2, batch_length: int = 1):
    """
    Evaluates the performance between greedy algorithms with different module functions

    :param model_dist: The model distribution used to test with
    :param repeats: The number of testing repeats that are computed
    :param time_steps: The total number of time steps for tasks to arrive at
    :param mean_arrival_rate: The mean arrival rate of tasks
    :param std_arrival_rate: The standard deviation of the arrival rate for the task
    :param batch_length: The batch length of the testing setting
    """
    print(f'Evaluates performance between different greedy permutations')
    print(f'Settings - Time steps: {time_steps}, mean arrival rate: {mean_arrival_rate}, std: {std_arrival_rate}')
    model_results = []

    filename = results_filename('online_greedy_permutations', model_dist)
    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        # Generate the tasks and servers
        tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
        algorithm_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}

        valid_tasks = [task for task in tasks if batch_length < task.deadline]
        batched_tasks = generate_batch_tasks(valid_tasks, batch_length, time_steps)
        flattened_tasks = [task for tasks in batched_tasks for task in tasks]

        for task_priority, server_selection, resource_allocation in [
            (UtilityDeadlinePerResourcePriority(ResourceSumPriority()), ProductResources(), SumPowPercentage()),
            (UtilityDeadlinePerResourcePriority(ResourceSumPriority()), ProductResources(True), SumPowPercentage()),

            (UtilityDeadlinePerResourcePriority(ResourceProductPriority()), ProductResources(), SumPowPercentage()),
            (UtilityDeadlinePerResourcePriority(ResourceProductPriority()), ProductResources(True), SumPowPercentage()),

            (ValuePriority(), ProductResources(), SumPowPercentage()),
            (ValuePriority(), ProductResources(), SumPowPercentage()),

            (UtilityDeadlinePerResourcePriority(ResourceSumPriority()), SumResources(), SumPowPercentage()),
            (UtilityDeadlinePerResourcePriority(ResourceSumPriority()), SumResources(True), SumPowPercentage())
        ]:
            greedy_name = f'Greedy {task_priority.name}, {server_selection.name}, ' \
                          f'{resource_allocation.name}'
            greedy_result = online_batch_solver(batched_tasks, servers, batch_length, greedy_name,
                                                greedy_algorithm, task_priority=task_priority,
                                                server_selection=server_selection,
                                                resource_allocation=resource_allocation)
            algorithm_results[greedy_result.algorithm] = greedy_result.store()
            print(greedy_name)
            reset_model(flattened_tasks, servers)

        model_results.append(algorithm_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


if __name__ == "__main__":
    args = parse_args()

    if args.model == 'alibaba':
        online_evaluation(get_model(args.model, args.tasks, args.servers),
                          time_steps=500, mean_arrival_rate=1.5, std_arrival_rate=1)
    elif args.model == 'synthetic':
        online_evaluation(get_model(args.model, args.tasks, args.servers),
                          time_steps=250, mean_arrival_rate=3, std_arrival_rate=1)
    else:
        if args.extra == 'greedy':
            print(f'Running greedy permutations for {args.model}')
            if args.model == 'alibaba':
                greedy_permutations(get_model(args.model, args.tasks, args.servers),
                                    time_steps=500, mean_arrival_rate=1.5, std_arrival_rate=1)
            elif args.model == 'synthetic':
                online_evaluation(get_model(args.model, args.tasks, args.servers),
                                  time_steps=250, mean_arrival_rate=3, std_arrival_rate=1)
        else:
            online_evaluation(get_model(args.model, args.tasks, args.servers))
