"""
Investigates the effectiveness of elastic vs non-elastic resource speeds for a range of capacity ratios
"""

from __future__ import annotations

import json
from pprint import PrettyPrinter
from typing import Iterable, Optional

from src.core.core import reset_model
from src.extra.io import parse_args, results_filename
from src.extra.model import ModelDist, get_model, generate_evaluation_model
from src.greedy.greedy import greedy_permutations
from src.optimal.non_elastic_optimal import non_elastic_optimal
from src.optimal.elastic_optimal import elastic_optimal


# noinspection DuplicatedCode
def server_resource_ratio(model_dist: ModelDist, repeat_num: int, repeats: int = 25, run_elastic: bool = True,
                          run_non_elastic: bool = True, non_elastic_time_limit: Optional[int] = None,
                          ratios: Iterable[int] = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)):
    """
    Evaluates the difference in social welfare when the ratio of computational to bandwidth capacity is changed between
        different algorithms: greedy, elastic optimal, non-elastic optimal and server relaxed optimal

    :param model_dist: The model distribution
    :param repeat_num: The repeat number
    :param repeats: The number of repeats
    :param run_elastic: If to run the optimal elastic solver
    :param run_non_elastic: If to run the optimal non-elastic solver
    :param non_elastic_time_limit: The non-elastic optimal time limit
    :param ratios: List of ratios to test
    """
    pretty_printer, model_results = PrettyPrinter(), []
    filename = results_filename('resource_ratio', model_dist, repeat_num)

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        # Generate the tasks and servers
        tasks, servers, non_elastic_tasks, ratio_results = generate_evaluation_model(model_dist, pretty_printer)

        server_total_resources = {server: server.computation_capacity + server.bandwidth_capacity
                                  for server in servers}
        for ratio in ratios:
            algorithm_results = {}
            # Update server capacities
            for server in servers:
                server.update_capacities(int(server_total_resources[server] * ratio),
                                         int(server_total_resources[server] * (1 - ratio)))

            if run_elastic:
                # Finds the elastic optimal solution
                elastic_optimal_results = elastic_optimal(tasks, servers, time_limit=None)
                algorithm_results[elastic_optimal_results.algorithm] = elastic_optimal_results.store(ratio=ratio)
                pretty_printer.pprint(algorithm_results[elastic_optimal_results.algorithm])
                reset_model(tasks, servers)

            if run_non_elastic:
                # Find the non-elastic optimal solution
                non_elastic_results = non_elastic_optimal(non_elastic_tasks, servers, time_limit=non_elastic_time_limit)
                algorithm_results[non_elastic_results.algorithm] = non_elastic_results.store(ratio=ratio)
                non_elastic_results.pretty_print()
                reset_model(non_elastic_tasks, servers)

            # Loop over all of the greedy policies permutations
            greedy_permutations(tasks, servers, algorithm_results)

            ratio_results[f'ratio {ratio}'] = algorithm_results
        model_results.append(ratio_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


if __name__ == "__main__":
    args = parse_args()
    if args.extra == '' or args.extra == 'elastic optimal':
        server_resource_ratio(get_model(args.model, args.tasks, args.servers), args.repeat)
    elif args.extra == 'non-elastic optimal':
        server_resource_ratio(get_model(args.model, args.tasks, args.servers), args.repeat, run_elastic=False)
    elif args.extra == 'time limited':
        server_resource_ratio(get_model(args.model, args.tasks, args.servers), args.repeat,
                              run_elastic=False, run_non_elastic=True, non_elastic_time_limit=60)
