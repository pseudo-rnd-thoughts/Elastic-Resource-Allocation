"""
Tests the greedy testing
Todo add greedy testing for greedy and matrix greedy optimisations
"""

from __future__ import annotations

import numpy as np

from core.core import reset_model
from extra.model import ModelDistribution
from greedy.matrix_allocation_policy import SumServerMaxPercentage
from greedy.greedy import greedy_algorithm
from greedy.matrix_greedy import greedy_matrix_algorithm
from greedy.resource_allocation_policy import SumPercentage, policies as resource_allocation_policies
from greedy.server_selection_policy import SumResources, all_policies as server_selection_policies
from greedy.task_prioritisation import UtilityDeadlinePerResource, all_policies as value_density_policies


def test_greedy_policies():
    print()
    model = ModelDistribution('../models/synthetic.mdl', 20, 3)
    tasks, servers = model.generate()

    policy_results = {}

    print('Policies')
    for value_density in value_density_policies:
        for server_selection_policy in server_selection_policies:
            for resource_allocation_policy in resource_allocation_policies:
                reset_model(tasks, servers)

                result = greedy_algorithm(tasks, servers, value_density, server_selection_policy,
                                          resource_allocation_policy)
                print(f'\t{result.algorithm} - {result.data["solve time"]} secs')
                if result.algorithm in policy_results:
                    policy_results[result.algorithm].append(result)
                else:
                    policy_results[result.algorithm] = [result]

    print('\n\nSorted policies by social welfare')
    for algorithm, results in policy_results.items():
        policy_results[algorithm] = (policy_results[algorithm],
                                     float(np.mean([r.social_welfare for r in results])),
                                     float(np.mean([r.solve_time for r in results])))
    print(f'Algorithm | Avg SW | Avg Time | Social Welfare')
    for algorithm, (results, avg_sw, avg_time) in sorted(policy_results.items(), key=lambda r: r[1]):
        print(f'{algorithm} | {avg_sw} | {avg_time} | [{" ".join([result.sum_value for result in results])}]')


def test_optimisation(repeats: int = 10):
    """
    Compare the greedy and greedy matrix algorithm, particular in terms of solve time and social welfare#

    :param repeats: Number of repeats
    """
    model = ModelDistribution('../models/synthetic.mdl', 20, 3)

    greedy_results, greedy_matrix_time = [], []
    print(f' Greedy     | Greedy Matrix')
    print(f' Time | Sum | Time   | Sum')
    for repeat in range(repeats):
        tasks, servers = model.generate()

        greedy_result = greedy_algorithm(tasks, servers, UtilityDeadlinePerResource(), SumResources(), SumPercentage())
        greedy_results.append(greedy_result)

        reset_model(tasks, servers)
        greedy_matrix_results = greedy_matrix_algorithm(tasks, servers, SumServerMaxPercentage())

        print(f'{str(greedy_result.data["solve time"]):5} | {greedy_result.social_welfare:3} | '
              f'{str(greedy_matrix_results.data["solve time"]):5} | {greedy_matrix_results.social_welfare:3}')


if __name__ == "__main__":
    test_greedy_policies()
