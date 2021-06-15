"""
Tests the realistic settings
"""

import json
from typing import List, Tuple

from src.core.core import reset_model
from src.core.non_elastic_task import generate_non_elastic_tasks
from src.extra.io import parse_args, results_filename
from src.extra.model import AlibabaModelDist
from src.greedy.greedy import greedy_permutations, greedy_algorithm
from src.greedy.resource_allocation import SumPercentage
from src.greedy.server_selection import SumResources
from src.greedy.task_priority import UtilityDeadlinePerResourcePriority
from src.optimal.non_elastic_optimal import non_elastic_optimal
from src.optimal.elastic_optimal import elastic_optimal


def model_scaling(model_dist: AlibabaModelDist, repeat_num: int, scaling: List[Tuple[int, int, int]],
                  repeats: int = 50):
    """
    Tests a range of possible model scaling

    :param model_dist: Model distribution
    :param repeat_num: The repeat number
    :param scaling: List of possible scaling
    :param repeats: The number of repeats
    """
    scaling_results = {}
    filename = results_filename('model_scaling', model_dist, repeat_num)
    greedy_params = (UtilityDeadlinePerResourcePriority(), SumResources(), SumPercentage())

    for storage_scaling, computation_scaling, results_scaling in scaling:
        print(f'Storage scaling: {storage_scaling}, computational scaling: {computation_scaling}, '
              f'results data scaling: {results_scaling}')
        model_dist.storage_scaling = storage_scaling
        model_dist.computational_scaling = computation_scaling
        model_dist.results_scaling = results_scaling

        model_results = []
        for _ in range(repeats):
            # Generate the tasks
            servers = [model_dist.generate_server(server_id) for server_id in range(model_dist.num_servers)]
            foreknowledge_tasks, requested_tasks = model_dist.generate_foreknowledge_requested_tasks(
                servers, model_dist.num_tasks)
            fixed_foreknowledge_tasks = generate_non_elastic_tasks(foreknowledge_tasks)
            fixed_requested_tasks = generate_non_elastic_tasks(requested_tasks)
            algorithm_results = {
                'model': {
                    'foreknowledge tasks': [task.save() for task in foreknowledge_tasks],
                    'fixed foreknowledge tasks': [task.save() for task in fixed_foreknowledge_tasks],
                    'requested tasks': [task.save() for task in requested_tasks],
                    'fixed requested task': [task.save() for task in fixed_requested_tasks],
                    'servers': [server.save() for server in servers]
                }
            }

            # Run the algorithms
            results = non_elastic_optimal(fixed_foreknowledge_tasks, servers, time_limit=60)
            algorithm_results['foreknowledge fixed optimal'] = results.store()
            reset_model(fixed_foreknowledge_tasks, servers)

            result = greedy_algorithm(foreknowledge_tasks, servers, *greedy_params)
            algorithm_results['foreknowledge greedy'] = result.store()
            reset_model(foreknowledge_tasks, servers)

            results = non_elastic_optimal(fixed_requested_tasks, servers, time_limit=60)
            algorithm_results['requested fixed optimal'] = results.store()
            reset_model(fixed_requested_tasks, servers)

            result = greedy_algorithm(requested_tasks, servers, *greedy_params)
            algorithm_results['requested greedy'] = result.store()
            reset_model(requested_tasks, servers)

            model_results.append(algorithm_results)
        scaling_results[f'{storage_scaling} {computation_scaling} {results_scaling}'] = model_results

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(scaling_results, file)


def foreknowledge_evaluation(model_dist: AlibabaModelDist, repeat_num: int, repeats: int = 50,
                             run_elastic: bool = False):
    filename = results_filename('foreknowledge', model_dist, repeat_num)
    model_results = []
    for _ in range(repeats):
        servers = [model_dist.generate_server(server_id) for server_id in range(model_dist.num_servers)]
        foreknowledge_tasks, requested_tasks = model_dist.generate_foreknowledge_requested_tasks(
            servers, model_dist.num_tasks)
        fixed_foreknowledge_tasks = generate_non_elastic_tasks(foreknowledge_tasks)
        fixed_requested_tasks = generate_non_elastic_tasks(requested_tasks)

        algorithm_results = {
            'model': {'foreknowledge tasks': [foreknowledge_task.save() for foreknowledge_task in foreknowledge_tasks],
                      'requested_tasks': [requested_task.save() for requested_task in requested_tasks],
                      'servers': [server.save() for server in servers]}}

        if run_elastic:
            results = elastic_optimal(foreknowledge_tasks, servers, time_limit=None)
            algorithm_results['foreknowledge flexible optimal'] = results.store()
            reset_model(foreknowledge_tasks, servers)

            results = elastic_optimal(requested_tasks, servers, time_limit=None)
            algorithm_results['requested flexible optimal'] = results.store()
            reset_model(requested_tasks, servers)

        results = non_elastic_optimal(fixed_foreknowledge_tasks, servers, time_limit=None)
        algorithm_results['foreknowledge fixed optimal'] = results.store()
        reset_model(fixed_foreknowledge_tasks, servers)

        results = non_elastic_optimal(fixed_requested_tasks, servers, time_limit=None)
        algorithm_results['requested fixed optimal'] = results.store()
        reset_model(fixed_requested_tasks, servers)

        greedy_permutations(foreknowledge_tasks, servers, algorithm_results, 'foreknowledge ')
        greedy_permutations(requested_tasks, servers, algorithm_results, 'requested ')

        model_results.append(algorithm_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished')


def task_sizing():
    model_dist = AlibabaModelDist(1000, 6)
    model_scales = {}
    for storage_scaling, computation_scaling, results_data_scaling in [
        (500, 1, 5), (500, 0.2, 5), (1000, 0.4, 10)
    ]:
        name = f'Storage: {storage_scaling}, computation: {computation_scaling}, results data: {results_data_scaling}'
        model_dist.storage_scaling = storage_scaling
        model_dist.computational_scaling = computation_scaling
        model_dist.results_scaling = results_data_scaling
        print(name)

        servers = [model_dist.generate_server(server_id) for server_id in range(model_dist.num_servers)]

        foreknowledge_tasks, requested_tasks = model_dist.generate_foreknowledge_requested_tasks(
            servers, model_dist.num_tasks)

        fixed_foreknowledge_tasks = generate_non_elastic_tasks(foreknowledge_tasks)
        fixed_requested_tasks = generate_non_elastic_tasks(requested_tasks)

        model_scales[name] = {
            'servers': [server.save() for server in servers],

            'foreknowledge tasks': [task.save() for task in foreknowledge_tasks],
            'fixed foreknowledge tasks': [task.save() for task in fixed_foreknowledge_tasks],

            'requested tasks': [task.save() for task in requested_tasks],
            'fixed requested tasks': [task.save() for task in fixed_requested_tasks]
        }

    with open('model_scaling.json', 'w') as file:
        json.dump(model_scales, file)


if __name__ == "__main__":
    args = parse_args()

    if args.extra == 'foreknowledge flexible':
        foreknowledge_evaluation(AlibabaModelDist(args.tasks, args.servers), args.repeat, run_elastic=True)
    elif args.extra == 'foreknowledge fixed':
        foreknowledge_evaluation(AlibabaModelDist(args.tasks, args.servers), args.repeat, run_elastic=False)
    elif args.extra == 'task sizing':
        task_sizing()
