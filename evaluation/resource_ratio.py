"""
Investigates the effectiveness of elastic vs fixed resource speeds
"""

from __future__ import annotations

import json
import pprint
from typing import Iterable

from core.core import reset_model
from core.fixed_task import FixedTask, FixedSumSpeeds
from extra.io import parse_args
from extra.model import ModelDistribution, results_filename
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import policies as resource_allocation_policies
from greedy.server_selection_policy import policies as server_selection_policies
from greedy.value_density import policies as value_densities
from optimal.fixed_optimal import fixed_optimal
from optimal.optimal import optimal
from optimal.relaxed import relaxed


def server_resource_ratio(model_dist: ModelDistribution, repeat_num: int, repeats: int = 10,
                          optimal_time_limit: int = 15, fixed_optimal_time_limit: int = 15, relaxed_time_limit: int = 15,
                          ratios: Iterable[int] = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)):
    model_results = []
    pp = pprint.PrettyPrinter()

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        # Generate the tasks and servers
        tasks, servers = model_dist.generate()
        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]
        ratio_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}
        pp.pprint(ratio_results)

        server_total_resources = {server: server.computation_capacity + server.bandwidth_capacity for server in servers}
        for ratio in ratios:
            algorithm_results = {}
            # Update server capacities
            for server in servers:
                server.update_capacities(int(server_total_resources[server] * ratio),
                                         int(server_total_resources[server] * (1 - ratio)))

            # Optimal
            optimal_result = optimal(tasks, servers, optimal_time_limit)
            algorithm_results[optimal_result.algorithm] = optimal_result.store(ratio=ratio)
            optimal_result.pretty_print()
            reset_model(tasks, servers)

            # Fixed optimal
            fixed_optimal_result = fixed_optimal(fixed_tasks, servers, fixed_optimal_time_limit)
            algorithm_results[fixed_optimal_result.algorithm] = fixed_optimal_result.store(ratio=ratio)
            fixed_optimal_result.pretty_print()
            reset_model(fixed_tasks, servers)

            # Find the relaxed solution
            relaxed_result = relaxed(tasks, servers, relaxed_time_limit)
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

            ratio_results[f'ratio {ratio}'] = algorithm_results
        model_results.append(ratio_results)

        # Save the results to the file
        filename = results_filename('server_resource_ratio', model_dist, repeat_num)
        with open(filename, 'w') as file:
            json.dump(model_results, file)


if __name__ == "__main__":
    args = parse_args()
    loaded_model_dist = ModelDistribution(args['model'], args['tasks'], args['servers'])

    server_resource_ratio(loaded_model_dist, args['repeat'])
