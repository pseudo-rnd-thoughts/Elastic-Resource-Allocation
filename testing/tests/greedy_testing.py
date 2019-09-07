"""Tests to run on Southampton's Iridis 4 supercomputer"""

from __future__ import annotations

import json
import sys
from tqdm import tqdm

from core.model import reset_model, ModelDist, load_dist
from core.result import Result

from optimal.optimal import optimal_algorithm
from optimal.relaxed import relaxed_algorithm
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import policies as resource_allocation_policies
from greedy.server_selection_policy import policies as server_selection_policies
from greedy.value_density import policies as value_densities
from greedy_matrix.matrix_greedy import matrix_greedy
from greedy_matrix.allocation_value_policy import policies as matrix_policies


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

        optimal_result = optimal_algorithm(jobs, servers, time_limit=60)
        if optimal_result is None:
            print("No feasible solution found")
            continue
        results['Optimal'] = optimal_result.store()
        reset_model(jobs, servers)

        relaxed_result = relaxed_algorithm(jobs, servers, time_limit=60)
        if relaxed_result is not None:
            results['Relaxed'] = relaxed_result.store()
        else:
            print("No feasible relaxation solution found")
        reset_model(jobs, servers)

        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(jobs, servers,
                                                     value_density, server_selection_policy, resource_allocation_policy)
                    results['Greedy {}, {}, {}'.format(value_density.name, server_selection_policy.name,
                                                       resource_allocation_policy.name)] = greedy_result.store()
                    reset_model(jobs, servers)

        for policy in matrix_policies:
            greedy_matrix_result = matrix_greedy(jobs, servers, policy)
            results['Greedy matrix ' + policy.name] = greedy_matrix_result.store()
            reset_model(jobs, servers)

        data.append(results)

    with open('optimal_greedy_test_{}.txt'.format(model_dist.file_name), 'w') as json_file:
        json.dump(data, json_file)
    print(data)


def no_optimal_greedy_test(model_dist: ModelDist, repeats=200):
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
    num_jobs = int(sys.argv[1])
    num_servers = int(sys.argv[2])

    model_name, job_dist, server_dist = load_dist('models/basic.model')
    basic_model_dist = ModelDist(model_name, job_dist, num_jobs, server_dist, num_servers)

    optimal_greedy_test(basic_model_dist)
    # no_optimal_greedy_test(basic_model_dist)
