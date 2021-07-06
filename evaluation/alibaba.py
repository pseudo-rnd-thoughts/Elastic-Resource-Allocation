"""
Tests the realistic settings
"""

import json
from pprint import PrettyPrinter

from src.core.core import reset_model
from src.core.non_elastic_task import generate_non_elastic_tasks
from src.extra.io import parse_args, results_filename
from src.extra.model import AlibabaModelDist, generate_evaluation_model
from src.greedy.greedy import greedy_permutations
from src.optimal.elastic_optimal import elastic_optimal
from src.optimal.non_elastic_optimal import non_elastic_optimal


def foreknowledge_evaluation(model_dist: AlibabaModelDist, repeat_num: int, repeats: int = 50,
                             run_elastic: bool = False):
    filename = results_filename('foreknowledge', model_dist, repeat_num)
    model_results = []
    for _ in range(repeats):
        servers = [model_dist.generate_server(server_id) for server_id in range(model_dist.num_servers)]
        foreknowledge_tasks, requested_tasks = model_dist.generate_foreknowledge_requested_tasks(
            servers, model_dist.num_tasks)
        non_elastic_foreknowledge_tasks = generate_non_elastic_tasks(foreknowledge_tasks)
        non_elastic_requested_tasks = generate_non_elastic_tasks(requested_tasks)

        algorithm_results = {
            'model': {'foreknowledge tasks': [foreknowledge_task.save() for foreknowledge_task in foreknowledge_tasks],
                      'requested tasks': [requested_task.save() for requested_task in requested_tasks],
                      'servers': [server.save() for server in servers]}}

        if run_elastic:
            results = elastic_optimal(foreknowledge_tasks, servers, time_limit=None)
            algorithm_results['foreknowledge elastic optimal'] = results.store()
            reset_model(foreknowledge_tasks, servers)

            results = elastic_optimal(requested_tasks, servers, time_limit=None)
            algorithm_results['requested elastic optimal'] = results.store()
            reset_model(requested_tasks, servers)

        results = non_elastic_optimal(non_elastic_foreknowledge_tasks, servers, time_limit=None)
        algorithm_results['foreknowledge non-elastic optimal'] = results.store()
        reset_model(non_elastic_foreknowledge_tasks, servers)

        results = non_elastic_optimal(non_elastic_requested_tasks, servers, time_limit=None)
        algorithm_results['requested non-elastic optimal'] = results.store()
        reset_model(non_elastic_requested_tasks, servers)

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
        (500, 1, 5), (500, 0.2, 5), (1000, 0.5, 10)
    ]:
        name = f'Storage: {storage_scaling}, computation: {computation_scaling}, results data: {results_data_scaling}'
        model_dist.storage_scaling = storage_scaling
        model_dist.computational_scaling = computation_scaling
        model_dist.results_scaling = results_data_scaling

        servers = [model_dist.generate_server(server_id) for server_id in range(model_dist.num_servers)]

        foreknowledge_tasks, requested_tasks = model_dist.generate_foreknowledge_requested_tasks(
            servers, model_dist.num_tasks)

        non_elastic_foreknowledge_tasks = generate_non_elastic_tasks(foreknowledge_tasks)
        non_elastic_requested_tasks = generate_non_elastic_tasks(requested_tasks)

        model_scales[name] = {
            'servers': [server.save() for server in servers],

            'elastic foreknowledge tasks': [task.save() for task in foreknowledge_tasks],
            'non-elastic foreknowledge tasks': [task.save() for task in non_elastic_foreknowledge_tasks],

            'elastic requested tasks': [task.save() for task in requested_tasks],
            'non-elastic requested tasks': [task.save() for task in non_elastic_requested_tasks]
        }

    with open('model_scaling.json', 'w') as file:
        json.dump(model_scales, file)


def server_sizing(repeats: int = 20):
    model_dist = AlibabaModelDist(20, 4)
    pretty_printer, server_scales = PrettyPrinter(), {}

    for mean_storage, mean_computation, mean_bandwidth in ((400, 50, 120), (400, 60, 150), (400, 70, 160)):
        model_dist.model['server distributions'] = [{
            "name": "custom",
            "probability": 1,
            "storage mean": mean_storage, "storage std": 30,
            "computation mean": mean_computation, "computation std": 8,
            "bandwidth mean": mean_bandwidth, "bandwidth std": 15
        }]
        model_results = []
        for _ in range(repeats):
            tasks, servers, non_elastic_tasks, algorithm_results = generate_evaluation_model(model_dist, pretty_printer)

            non_elastic_results = non_elastic_optimal(non_elastic_tasks, servers, time_limit=60)
            algorithm_results[non_elastic_results.algorithm] = non_elastic_results.store()
            reset_model(non_elastic_tasks, servers)

            greedy_permutations(tasks, servers, algorithm_results)

            model_results.append(algorithm_results)

        server_scales[f'{mean_storage}, {mean_computation}, {mean_bandwidth}'] = model_results

        with open('server_scaling_3.json', 'w') as file:
            json.dump(server_scales, file)


if __name__ == "__main__":
    args = parse_args()

    if args.extra == 'foreknowledge elastic':
        foreknowledge_evaluation(AlibabaModelDist(args.tasks, args.servers), args.repeat, run_elastic=True)
    elif args.extra == 'foreknowledge non-elastic':
        foreknowledge_evaluation(AlibabaModelDist(args.tasks, args.servers), args.repeat, run_elastic=False)
    elif args.extra == 'task sizing':
        task_sizing()
    if args.extra == 'server sizing':
        server_sizing()
