"""Tests to run on Southampton's Iridis 4 supercomputer"""

from __future__ import annotations

import json
from tqdm import tqdm

from core.model import reset_model, ModelDist, load_dist

from optimal.optimal import optimal_algorithm

from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import policies as resource_allocation_policies
from greedy.server_selection_policy import policies as server_selection_policies
from greedy.value_density import policies as value_densities
from greedy_matrix.matrix_greedy import matrix_greedy
from greedy_matrix.matrix_policy import policies as matrix_policies


def greedy_test(model_dist, name, repeats=200):
    """Greedy tests"""
    data = []

    for _ in tqdm(range(repeats)):
        jobs, servers = model_dist.create()
        results = {}
        
        optimal_result = optimal_algorithm(jobs, servers, time_limit=15)
        if optimal_result is None:
            print("No feasible solution found")
            continue
        
        results['Optimal'] = optimal_result.total_utility
        reset_model(jobs, servers)
        
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(jobs, servers, value_density, server_selection_policy,
                                                     resource_allocation_policy)
                    results['Greedy {} {} {}'.format(value_density.name, server_selection_policy.name,
                                                     resource_allocation_policy.name)] = greedy_result.total_utility
                    reset_model(jobs, servers)

        for policy in matrix_policies:
            greedy_matrix_result = matrix_greedy(jobs, servers, policy)
            results['Matrix ' + policy.name] = greedy_matrix_result.total_utility
            reset_model(jobs, servers)

        # print(results)
        data.append(results)

    with open('greedy_results_{}.txt'.format(name), 'w') as outfile:
        json.dump(data, outfile)
    print("Model {} results".format(name))
    print(data)


if __name__ == "__main__":
    print("Greedy Testing")
    model_name, job_dist, server_dist = load_dist('models/basic.model')
    for num_jobs, num_servers in ((12, 2), (15, 3), (25, 5), (100, 20), (150, 25)):
        model_dist = ModelDist(model_name, job_dist, num_jobs, server_dist, num_servers)

        greedy_test(model_dist, 'Jobs {} servers {}'.format(num_jobs, num_servers))
