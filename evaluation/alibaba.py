"""
Tests the realistic settings
"""

import json
from typing import List, Tuple

from extra.model import AlibabaModelDist
from src.core.core import reset_model
from src.core.fixed_task import generate_fixed_tasks
from src.extra.io import parse_args, results_filename
from src.greedy.greedy import greedy_permutations
from src.optimal.fixed_optimal import fixed_optimal
from src.optimal.flexible_optimal import flexible_optimal


def model_scaling(model_dist: AlibabaModelDist, repeat_num: int, scaling: List[Tuple[int, int, int]],
                  repeats: int = 10):
    """
    Tests a range of possible model scaling

    :param model_dist: Model distribution
    :param repeat_num: The repeat number
    :param scaling: List of possible scaling
    :param repeats: The number of repeats
    """
    scaling_results = {}
    filename = results_filename('model_scaling', model_dist, repeat_num)

    for storage_scaling, computation_scaling, results_scaling in scaling:
        print(f'Storage scaling: {storage_scaling}, computational scaling: {computation_scaling}, '
              f'results data scaling: {results_scaling}')
        model_dist.storage_scaling = storage_scaling
        model_dist.computational_scaling = computation_scaling
        model_dist.results_scaling = results_scaling

        model_results = []
        for _ in range(repeats):
            servers = [model_dist.generate_server(server_id) for server_id in range(model_dist.num_servers)]
            foreknowledge_tasks, requested_tasks = model_dist.generate_foreknowledge_requested_tasks(servers, model_dist.num_tasks)
            fixed_foreknowledge_tasks = generate_fixed_tasks(foreknowledge_tasks)
            fixed_requested_tasks = generate_fixed_tasks(requested_tasks)
            algorithm_results = {
                'model': {
                    'foreknowledge tasks': [foreknowledge_task.save() for foreknowledge_task in foreknowledge_tasks],
                    'requested_tasks': [requested_task.save() for requested_task in requested_tasks],
                    'servers': [server.save() for server in servers]}}

            results = fixed_optimal(fixed_foreknowledge_tasks, servers, time_limit=60)
            algorithm_results['foreknowledge fixed optimal'] = results.store()
            reset_model(fixed_foreknowledge_tasks, servers)

            results = fixed_optimal(fixed_requested_tasks, servers, time_limit=60)
            algorithm_results['requested fixed optimal'] = results.store()
            reset_model(fixed_requested_tasks, servers)

            greedy_permutations(foreknowledge_tasks, servers, algorithm_results, 'foreknowledge')
            greedy_permutations(requested_tasks, servers, algorithm_results, 'requested')

            model_results.append(algorithm_results)

        scaling_results[f'{storage_scaling} {computation_scaling} {results_scaling}'] = model_results

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(scaling_results, file)


def foreknowledge_evaluation(model_dist: AlibabaModelDist, repeat_num: int, repeats: int = 50,
                             run_flexible: bool = False):
    filename = results_filename('foreknowledge', model_dist, repeat_num)
    model_results = []
    for _ in range(repeats):
        servers = [model_dist.generate_server(server_id) for server_id in range(model_dist.num_servers)]
        foreknowledge_tasks, requested_tasks = model_dist.generate_foreknowledge_requested_tasks(servers, model_dist.num_tasks)
        fixed_foreknowledge_tasks = generate_fixed_tasks(foreknowledge_tasks)
        fixed_requested_tasks = generate_fixed_tasks(requested_tasks)
        algorithm_results = {
            'model': {'foreknowledge tasks': [foreknowledge_task.save() for foreknowledge_task in foreknowledge_tasks],
                      'requested_tasks': [requested_task.save() for requested_task in requested_tasks],
                      'servers': [server.save() for server in servers]}}

        if run_flexible:
            results = flexible_optimal(foreknowledge_tasks, servers, time_limit=None)
            algorithm_results['foreknowledge flexible optimal'] = results.store()
            reset_model(foreknowledge_tasks, servers)

            results = flexible_optimal(requested_tasks, servers, time_limit=None)
            algorithm_results['requested flexible optimal'] = results.store()
            reset_model(requested_tasks, servers)

        results = fixed_optimal(fixed_foreknowledge_tasks, servers, time_limit=None)
        algorithm_results['foreknowledge fixed optimal'] = results.store()
        reset_model(fixed_foreknowledge_tasks, servers)

        results = fixed_optimal(fixed_requested_tasks, servers, time_limit=None)
        algorithm_results['requested fixed optimal'] = results.store()
        reset_model(fixed_requested_tasks, servers)

        greedy_permutations(foreknowledge_tasks, servers, algorithm_results, 'foreknowledge')
        greedy_permutations(requested_tasks, servers, algorithm_results, 'requested')

        model_results.append(algorithm_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished')


def task_sizing(model_dist: AlibabaModelDist, repeat_num: int):
    filename = results_filename('task_sizing', model_dist, repeat_num)
    servers = [model_dist.generate_server(server_id) for server_id in range(model_dist.num_servers)]

    foreknowledge_tasks, requested_tasks = model_dist.generate_foreknowledge_requested_tasks(servers, model_dist.num_tasks)
    fixed_foreknowledge_tasks = generate_fixed_tasks(foreknowledge_tasks)
    fixed_requested_tasks = generate_fixed_tasks(requested_tasks)

    model_results = {'server': [server.save() for server in servers],
                     'requested-tasks': [task.save(more=True) for task in fixed_requested_tasks],
                     'foreknowledge-tasks': [task.save(more=True) for task in fixed_foreknowledge_tasks]}

    # Save the results to the file
    with open(filename, 'w') as file:
        json.dump(model_results, file)
    print('Finished')


if __name__ == "__main__":
    args = parse_args()

    if args.extra == 'foreknowledge flexible':
        foreknowledge_evaluation(AlibabaModelDist(args.tasks, args.servers), args.repeat, run_flexible=True)
    elif args.extra == 'foreknowledge fixed':
        foreknowledge_evaluation(AlibabaModelDist(args.tasks, args.servers), args.repeat, run_flexible=False)
    elif args.extra == 'model sizing':
        model_scaling(AlibabaModelDist(args.tasks, args.servers), args.repeat,
                      [(500, 1, 5), (250, 1, 2.5), (300, 0.6, 5)])
    elif args.extra == 'task sizing':
        task_sizing(AlibabaModelDist(args.tasks, args.servers), args.repeat)
