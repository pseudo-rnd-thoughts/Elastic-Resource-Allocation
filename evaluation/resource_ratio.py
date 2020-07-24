"""
Investigates the effectiveness of elastic vs fixed resource speeds
"""

from __future__ import annotations

import json
import pprint
from typing import Iterable

from greedy.fixed_greedy import fixed_greedy_algorithm
from optimal.server_relaxed_flexible_optimal import server_relaxed_flexible_optimal
from src.core.core import reset_model
from src.core.fixed_task import FixedTask, SumSpeedPowsFixedPolicy
from src.extra.io import parse_args, results_filename
from src.extra.model import ModelDistribution
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import policies as resource_allocation_policies
from src.greedy.server_selection_policy import policies as server_selection_policies
from src.greedy.value_density import policies as value_densities
from src.optimal.fixed_optimal import fixed_optimal
from src.optimal.flexible_optimal import flexible_optimal


# noinspection DuplicatedCode
def server_resource_ratio(model_dist: ModelDistribution, repeat_num: int, repeats: int = 25,
                          optimal_time_limit: int = 30, fixed_optimal_time_limit: int = 30,
                          relaxed_time_limit: int = 30, with_optimal: bool = False,
                          ratios: Iterable[int] = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)):
    """
    Evaluates the difference in social welfare when the ratio of computational to bandwidth capacity is changed between
        different algorithms: greedy, fixed, optimal and relax

    :param model_dist: The model distribution
    :param repeat_num: The repeat number
    :param repeats: The number of repeats
    :param optimal_time_limit: The optimal solver time limit
    :param fixed_optimal_time_limit: The fixed optimal solver time limit
    :param relaxed_time_limit: The relaxed solver time limit
    :param with_optimal: If to run the optimal algorithms
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

            if with_optimal:
                # Optimal
                optimal_result = flexible_optimal(tasks, servers, optimal_time_limit)
                algorithm_results[optimal_result.algorithm] = optimal_result.store(ratio=ratio)
                pp.pprint(algorithm_results[optimal_result.algorithm])
                reset_model(tasks, servers)

                # Fixed optimal
                fixed_optimal_result = fixed_optimal(fixed_tasks, servers, fixed_optimal_time_limit)
                algorithm_results[fixed_optimal_result.algorithm] = fixed_optimal_result.store(ratio=ratio)
                pp.pprint(algorithm_results[fixed_optimal_result.algorithm])
                reset_model(fixed_tasks, servers)

            # Find the relaxed solution
            relaxed_result = server_relaxed_flexible_optimal(tasks, servers, relaxed_time_limit)
            algorithm_results[relaxed_result.algorithm] = relaxed_result.store(ratio=ratio)
            pp.pprint(algorithm_results[relaxed_result.algorithm])
            reset_model(tasks, servers)

            # Loop over all of the greedy policies permutations
            for value_density in value_densities:
                for server_selection_policy in server_selection_policies:
                    for resource_allocation_policy in resource_allocation_policies:
                        greedy_result = greedy_algorithm(tasks, servers, value_density, server_selection_policy,
                                                         resource_allocation_policy)
                        algorithm_results[greedy_result.algorithm] = greedy_result.store(ratio=ratio)
                        pp.pprint(algorithm_results[greedy_result.algorithm])
                        reset_model(tasks, servers)

            # Loop over all of the fixed greedy policies permutations
            for value_density in value_densities:
                for server_selection_policy in server_selection_policies:
                    assert all(type(task) is FixedTask for task in fixed_tasks), ', '.join([str(type(task) for task in fixed_tasks)])
                    fixed_greedy_result = fixed_greedy_algorithm(fixed_tasks, servers, value_density,
                                                                 server_selection_policy)
                    algorithm_results[fixed_greedy_result.algorithm] = fixed_greedy_result.store()
                    fixed_greedy_result.pretty_print()
                    reset_model(fixed_tasks, servers)

            ratio_results[f'ratio {ratio}'] = algorithm_results
        model_results.append(ratio_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


if __name__ == "__main__":
    args = parse_args()
    server_resource_ratio(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
