"""
Tests the greedy testing
Todo add greedy testing for greedy and matrix greedy optimisations
"""

from __future__ import annotations

import numpy as np

from core.elastic_task import ElasticTask
from core.server import Server
from src.core.core import reset_model
from src.extra.model import SyntheticModelDist
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation import SumPercentage, resource_allocation_functions
from src.greedy.server_selection import server_selection_functions
from src.greedy.task_priority import task_priority_functions


def test_greedy_policies():
    print()
    model = SyntheticModelDist(20, 3)
    tasks, servers = model.generate_oneshot()

    policy_results = {}

    print('Policies')
    for value_density in task_priority_functions:
        for server_selection_policy in server_selection_functions:
            for resource_allocation_policy in resource_allocation_functions:
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
    for algorithm, (results, avg_sw, avg_time) in sorted(policy_results.items(), key=lambda r: r[1][1]):
        print(f'{algorithm} | {avg_sw} | {avg_time} | [{" ".join([str(result.social_welfare) for result in results])}]')


def test_failed_greedy_resource_allocation():
    # Exception: Resource allocation for a task is infeasible, model solution is Infeasible.
    # The task setting is {'name': 'Foreknowledge Task 10',
    # 'storage': 30, 'computation': 20, 'results data': 9, 'deadline': 17.0, 'value': 17.62}
    # and the server setting has available bandwidth of 34 and available computation of 16 (storage: 40)

    task = ElasticTask('test task', required_storage=30, required_computation=20, required_results_data=9,
                       deadline=17, value=17.62)
    server = Server('test server', storage_capacity=50, computation_capacity=50, bandwidth_capacity=50)
    server.available_storage = 40
    server.available_computation = 16
    server.available_bandwidth = 34

    print(server.can_run(task))

    resource_allocation = SumPercentage()
    _, _, _ = resource_allocation.allocate(task, server)


if __name__ == "__main__":
    test_greedy_policies()
