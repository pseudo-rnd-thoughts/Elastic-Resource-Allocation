"""Tests to run on Southampton's Iridis 4 supercomputer"""

from __future__ import annotations

import json
from typing import Dict, Tuple, List

from tqdm import tqdm

from core.core import load_args, results_filename
from core.fixed_job import FixedJob, FixedSumSpeeds
from core.job import Job
from core.model import reset_model, ModelDist, load_dist
from core.server import Server
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import policies as resource_allocation_policies
from greedy.server_selection_policy import policies as server_selection_policies
from greedy.value_density import all_policies as value_densities
from greedy_matrix.allocation_value_policy import policies as matrix_policies
from greedy_matrix.matrix_greedy import matrix_greedy
from optimal.fixed_optimal import fixed_optimal_algorithm
from optimal.optimal import optimal_algorithm
from optimal.relaxed import relaxed_algorithm


def best_algorithms_test(model_dist: ModelDist, repeat: int, repeats: int = 50,
                         optimal_time_limit: int = 30, fixed_time_limit: int = 30, relaxed_time_limit: int = 30):
    """
    Greedy test with optimal found
    :param model_dist: The model distribution
    :param repeat: The repeat
    :param repeats: Number of model runs
    :param optimal_time_limit: The compute time for the optimal algorithm
    :param fixed_time_limit: The compute time for the fixed optimal algorithm
    :param relaxed_time_limit: The compute time for the relaxed algorithm
    """
    print("Greedy test with optimal calculated for {} jobs and {} servers"
          .format(model_dist.num_jobs, model_dist.num_servers))
    data = []

    # Loop, for each run all of the algorithms
    for _ in tqdm(range(repeats)):
        # Generate the jobs and the servers
        jobs, servers = model_dist.create()
        algorithm_results = {}

        # Find the optimal solution
        optimal_result = optimal_algorithm(jobs, servers, optimal_time_limit)
        algorithm_results[optimal_result.algorithm_name] = optimal_result.store() \
            if optimal_result is not None else "failure"
        reset_model(jobs, servers)
        
        # Find the fixed solution
        fixed_jobs = [FixedJob(job, servers, FixedSumSpeeds()) for job in jobs]
        fixed_result = fixed_optimal_algorithm(fixed_jobs, servers, fixed_time_limit)
        algorithm_results[fixed_result.algorithm_name] = fixed_result.store() \
            if fixed_result is not None else "failure"
        reset_model(fixed_jobs, servers)

        # Find the relaxed solution
        relaxed_result = relaxed_algorithm(jobs, servers, relaxed_time_limit)
        algorithm_results[relaxed_result.algorithm_name] = relaxed_result.store() \
            if relaxed_result is not None else "failure"
        reset_model(jobs, servers)

        # Loop over all of the greedy policies permutations
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(jobs, servers, value_density, server_selection_policy,
                                                     resource_allocation_policy)
                    algorithm_results[greedy_result.algorithm_name] = greedy_result.store()
                    reset_model(jobs, servers)

        # Loop over all of the matrix policies
        for policy in matrix_policies:
            greedy_matrix_result = matrix_greedy(jobs, servers, policy)
            algorithm_results[greedy_matrix_result.algorithm_name] = greedy_matrix_result.store()
            reset_model(jobs, servers)

        # Add the results to the data
        data.append(algorithm_results)

    # Save the results to the file
    filename = results_filename('optimal_greedy_test', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print("Successful, data saved to " + filename)


def all_policies_test(model_dist: ModelDist, repeat: int, repeats: int = 200):
    """
    All policies test
    :param model_dist: The model distributions
    :param repeat: The repeat
    :param repeats: The number of repeats
    """
    print("Greedy test of all policies for {} jobs and {} servers"
          .format(model_dist.num_jobs, model_dist.num_servers))
    data = []

    # Loop, for each run all of the algorithms
    for _ in tqdm(range(repeats)):
        # Generate the jobs and the servers
        jobs, servers = model_dist.create()
        algorithm_results = {}

        # Loop over all of the greedy policies permutations
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(jobs, servers, value_density, server_selection_policy,
                                                     resource_allocation_policy)
                    algorithm_results[greedy_result.algorithm_name] = greedy_result.store()
                    reset_model(jobs, servers)

        # Add the results to the data
        data.append(algorithm_results)

    # Save the results to the file
    filename = results_filename('all_greedy_test', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print("Successful, data saved to " + filename)


def allocation_test(model_dist: ModelDist, repeat: int, repeats: int = 50,
                    optimal_time_limit: int = 300, relaxed_time_limit: int = 150):
    """
    Allocation test
    :param model_dist: The model distribution
    :param repeat: The repeat number
    :param repeats: The number of repeats
    :param optimal_time_limit: The optimal time limit
    :param relaxed_time_limit: The relaxed time limit
    """

    def job_data() -> Dict[str, Tuple[int, int, int, str]]:
        """
        Generate the important job data
        :return: The dictionary of job data
        """
        return {
            job.name: (job.loading_speed, job.compute_speed, job.sending_speed, job.running_server.name)
            for job in jobs if job.running_server
        }
    
    def model_data():
        """
        Generate the json for saving the model data usd
        :return: The json for the
        """
        return (
            {job.name: (job.required_storage, job.required_computation, job.required_results_data,
                        job.deadline, job.value) for job in jobs},
            {server.name: (server.storage_capacity, server.computation_capacity, server.bandwidth_capacity)
             for server in servers}
        )

    print("Allocation testing using the results of the greedy, relaxed and optimal{} jobs and {} servers"
          .format(model_dist.num_jobs, model_dist.num_servers))
    data = []

    # Loop, for each run all of the algorithms
    for _ in tqdm(range(repeats)):
        # Generate the jobs and the servers
        jobs, servers = model_dist.create()
        algorithm_results = {'model': model_data()}

        # Find the optimal solution
        optimal_result = optimal_algorithm(jobs, servers, optimal_time_limit)
        algorithm_results[optimal_result.algorithm_name] = optimal_result.store(jobs_data=job_data()) \
            if optimal_result is not None else "failure"
        reset_model(jobs, servers)

        # Find the relaxed solution
        relaxed_result = relaxed_algorithm(jobs, servers, relaxed_time_limit)
        algorithm_results[relaxed_result.algorithm_name] = relaxed_result.store(jobs_data=job_data()) \
            if relaxed_result is not None else "failure"
        reset_model(jobs, servers)

        # Loop over all of the greedy policies permutations
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(jobs, servers, value_density, server_selection_policy,
                                                     resource_allocation_policy)
                    algorithm_results[greedy_result.algorithm_name] = greedy_result.store(jobs_data=job_data())
                    reset_model(jobs, servers)

        # Loop over all of the matrix policies
        for policy in matrix_policies:
            greedy_matrix_result = matrix_greedy(jobs, servers, policy)
            algorithm_results[greedy_matrix_result.algorithm_name] = greedy_matrix_result.store(jobs_data=job_data())
            reset_model(jobs, servers)

        # Add the results to the data
        data.append(algorithm_results)

    # Save the results to the file
    filename = results_filename('optimal_greedy_test', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print("Successful, data saved to " + filename)


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    # best_algorithms_test(loaded_model_dist, args['repeat'])
    # allocation_test(loaded_model_dist, args['repeat'])
    all_policies_test(loaded_model_dist, args['repeat'])
