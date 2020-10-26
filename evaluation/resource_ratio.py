"""
Investigates the effectiveness of elastic vs fixed resource speeds
"""

from __future__ import annotations

import json
import pprint
from typing import Iterable

from src.core.core import reset_model
from src.core.fixed_task import FixedTask, SumSpeedPowsFixedPolicy
from src.extra.io import parse_args, results_filename
from src.extra.model import ModelDistribution
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import policies as resource_allocation_policies
from src.greedy.server_selection_policy import policies as server_selection_policies
from src.greedy.task_prioritisation import policies as task_priorities
from src.optimal.fixed_optimal import fixed_optimal
from src.optimal.flexible_optimal import flexible_optimal


# noinspection DuplicatedCode
def server_resource_ratio(model_dist: ModelDistribution, repeat_num: int, repeats: int = 25,
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
    model_results = []
    pp = pprint.PrettyPrinter()
    filename = results_filename('resource_ratio', model_dist, repeat_num)

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        # Generate the tasks and servers
        tasks, servers = model_dist.generate()
        fixed_tasks = [FixedTask(task, SumSpeedPowsFixedPolicy()) for task in tasks]
        ratio_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}
        pp.pprint(ratio_results)

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
                pp.pprint(algorithm_results[optimal_result.algorithm])
                reset_model(tasks, servers)

            if run_fixed:
                # Fixed optimal
                fixed_optimal_result = fixed_optimal(fixed_tasks, servers, None)
                algorithm_results[fixed_optimal_result.algorithm] = fixed_optimal_result.store(ratio=ratio)
                pp.pprint(algorithm_results[fixed_optimal_result.algorithm])
                reset_model(fixed_tasks, servers)

            # Loop over all of the greedy policies permutations
            for task_priority in task_priorities:
                for server_selection_policy in server_selection_policies:
                    for resource_allocation_policy in resource_allocation_policies:
                        greedy_result = greedy_algorithm(tasks, servers, task_priority, server_selection_policy,
                                                         resource_allocation_policy)
                        algorithm_results[greedy_result.algorithm] = greedy_result.store(ratio=ratio)
                        pp.pprint(algorithm_results[greedy_result.algorithm])
                        reset_model(tasks, servers)

            ratio_results[f'ratio {ratio}'] = algorithm_results
        model_results.append(ratio_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


if __name__ == "__main__":
    args = parse_args()
    if args.extra == '' or args.extra == 'full optimal':
        server_resource_ratio(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
    elif args.extra == 'fixed optimal':
        server_resource_ratio(ModelDistribution(args.file, args.tasks, args.servers), args.repeat, run_flexible=False)
    elif args.extra == 'time limited':
        server_resource_ratio(ModelDistribution(args.file, args.tasks, args.servers), args.repeat,
                              run_flexible=False, run_fixed=False)
