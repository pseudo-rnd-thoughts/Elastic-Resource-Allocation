"""
Investigates the effectiveness of elastic vs fixed resource speeds
"""

from __future__ import annotations

import json
from pprint import PrettyPrinter
from typing import Iterable

from src.core.core import reset_model
from src.extra.io import parse_args, results_filename
from src.extra.model import ModelDist, get_model, generate_evaluation_model
from src.greedy.greedy import greedy_permutations
from src.optimal.fixed_optimal import fixed_optimal
from src.optimal.flexible_optimal import flexible_optimal


# noinspection DuplicatedCode
def server_resource_ratio(model_dist: ModelDist, repeat_num: int, repeats: int = 25,
                          run_flexible: bool = True, run_fixed: bool = True,
                          ratios: Iterable[int] = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)):
    """
    Evaluates the difference in social welfare when the ratio of computational to bandwidth capacity is changed between
        different algorithms: greedy, fixed, optimal and relax

    :param model_dist: The model distribution
    :param repeat_num: The repeat number
    :param repeats: The number of repeats
    :param run_flexible: If to run the optimal flexible solver
    :param run_fixed: If to run the optimal fixed solver
    :param ratios: List of ratios to test
    """
    pretty_printer, model_results = PrettyPrinter(), []
    filename = results_filename('resource_ratio', model_dist, repeat_num)

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        # Generate the tasks and servers
        tasks, servers, fixed_tasks, ratio_results = generate_evaluation_model(model_dist, pretty_printer)

        server_total_resources = {server: server.computation_capacity + server.bandwidth_capacity
                                  for server in servers}
        for ratio in ratios:
            algorithm_results = {}
            # Update server capacities
            for server in servers:
                server.update_capacities(int(server_total_resources[server] * ratio),
                                         int(server_total_resources[server] * (1 - ratio)))

            if run_flexible:
                # Optimal
                optimal_result = flexible_optimal(tasks, servers, None)
                algorithm_results[optimal_result.algorithm] = optimal_result.store(ratio=ratio)
                pretty_printer.pprint(algorithm_results[optimal_result.algorithm])
                reset_model(tasks, servers)

            if run_fixed:
                # Find the fixed solution
                fixed_optimal_result = fixed_optimal(fixed_tasks, servers, time_limit=None)
                algorithm_results[fixed_optimal_result.algorithm] = fixed_optimal_result.store()
                fixed_optimal_result.pretty_print()
                reset_model(fixed_tasks, servers)

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
    if args.extra == '' or args.extra == 'full optimal':
        server_resource_ratio(get_model(args.model, args.tasks, args.servers), args.repeat)
    elif args.extra == 'fixed optimal':
        server_resource_ratio(get_model(args.model, args.tasks, args.servers), args.repeat, run_flexible=False)
    elif args.extra == 'time limited':
        server_resource_ratio(get_model(args.model, args.tasks, args.servers), args.repeat,
                              run_flexible=False, run_fixed=False)
