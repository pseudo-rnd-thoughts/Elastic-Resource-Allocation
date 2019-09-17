"""Tests to run on Southampton's Iridis 4 supercomputer"""

from __future__ import annotations

import json

from tqdm import tqdm

from core.model import reset_model, ModelDist, load_dist
from core.core import load_args

from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import policies as resource_allocation_policies
from greedy.server_selection_policy import policies as server_selection_policies
from greedy.value_density import policies as value_densities

from greedy_matrix.allocation_value_policy import policies as matrix_policies
from greedy_matrix.matrix_greedy import matrix_greedy

from optimal.optimal import optimal_algorithm
from optimal.relaxed import relaxed_algorithm


def optimal_greedy_test(model_dist: ModelDist, repeats: int = 200):
    """
    Greedy test with optimal found
    :param model_dist: The model distribution
    :param repeats: Number of model runs
    """
    print("Greedy test with optimal calculated for {} jobs and {} servers".format(model_dist.num_jobs,
                                                                                  model_dist.num_servers))
    data = []

    for _ in tqdm(range(repeats)):
        jobs, servers = model_dist.create()
        results = {}

        optimal_result = optimal_algorithm(jobs, servers)
        results['Optimal'] = optimal_result.store() if optimal_result is None else "failure"
        reset_model(jobs, servers)

        relaxed_result = relaxed_algorithm(jobs, servers)
        results['Relaxed'] = relaxed_result.store() if relaxed_result is None else "failure"
        reset_model(jobs, servers)

        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(jobs, servers, value_density, server_selection_policy,
                                                     resource_allocation_policy)
                    results[greedy_result.algorithm_name] = greedy_result.store()
                    reset_model(jobs, servers)

        for policy in matrix_policies:
            greedy_matrix_result = matrix_greedy(jobs, servers, policy)
            results[greedy_matrix_result.algorithm_name] = greedy_matrix_result.store()
            reset_model(jobs, servers)

        data.append(results)

    with open('optimal_greedy_test_{}.txt'.format(model_dist.file_name), 'w') as json_file:
        json.dump(data, json_file)
    print(data)


def no_optimal_greedy_test(model_dist: ModelDist, repeats: int = 200):
    """No optimal greedy test"""
    print("Greedy test with no optimal calculated for {} jobs and {} servers".format(model_dist.num_jobs,
                                                                                     model_dist.num_servers))

    data = []
    for _ in tqdm(range(repeats)):
        result = {}
        jobs, servers = model_dist.create()

        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(jobs, servers, value_density, server_selection_policy,
                                                     resource_allocation_policy)
                    result['Greedy {}, {}, {}'.format(value_density.name, server_selection_policy.name,
                                                      resource_allocation_policy.name)] = greedy_result.store()
                    reset_model(jobs, servers)

        data.append(result)

    with open('no_optimal_greedy_test_{}.txt'.format(model_dist.file_name), 'w') as json_file:
        json.dump(data, json_file)
    print(data)
        
    
if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    basic_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    optimal_greedy_test(basic_model_dist,)
    # no_optimal_greedy_test(basic_model_dist)
