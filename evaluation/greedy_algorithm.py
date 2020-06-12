"""Tests to run on Southampton's Iridis 4 supercomputer"""

from __future__ import annotations

import json
from typing import Dict, Tuple

from tqdm import tqdm

from src.branch_bound.branch_bound import branch_bound_algorithm
from src.branch_bound.feasibility_allocations import fixed_feasible_allocation

from src.core.super_server import SuperServer
from src.core.core import results_filename, load_args, reset_model
from src.core.fixed_task import FixedTask, FixedSumSpeeds
from src.model.model_distribution import ModelDistribution, load_model_distribution

from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import policies as resource_allocation_policies
from src.greedy.resource_allocation_policy import SumPercentage, SumSpeed

from src.greedy.server_selection_policy import policies as server_selection_policies
from src.greedy.server_selection_policy import all_policies as all_server_selection_policies
from src.greedy.server_selection_policy import SumResources, TaskSumResources
from src.greedy.server_selection_policy import Random as RandomServerSelection

from src.greedy.value_density import policies as value_densities
from src.greedy.value_density import all_policies as all_value_densities
from src.greedy.value_density import UtilityPerResources, UtilityResourcePerDeadline, UtilityDeadlinePerResource, Value
from src.greedy.value_density import Random as RandomValueDensity

from src.greedy_matrix.allocation_value_policy import policies as matrix_policies
from src.greedy_matrix.matrix_greedy import matrix_greedy

from src.optimal.fixed_optimal import fixed_optimal_algorithm
from src.optimal.optimal import optimal_algorithm
from src.optimal.relaxed import relaxed_algorithm


def best_algorithms_test(model_dist: ModelDistribution, repeat: int, repeats: int = 50,
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
    print(f'Greedy test with optimal calculated for {model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    data = []

    # Loop, for each run all of the algorithms
    for _ in tqdm(range(repeats)):
        # Generate the tasks and the servers
        tasks, servers = model_dist.create()
        algorithm_results = {}

        # Find the optimal solution
        optimal_result = optimal_algorithm(tasks, servers, optimal_time_limit)
        algorithm_results[optimal_result.algorithm_name] = optimal_result.store() \
            if optimal_result is not None else 'failure'
        reset_model(tasks, servers)

        # Find the fixed solution
        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]
        fixed_result = fixed_optimal_algorithm(fixed_tasks, servers, fixed_time_limit)
        algorithm_results[fixed_result.algorithm_name] = fixed_result.store() \
            if fixed_result is not None else 'failure'
        reset_model(fixed_tasks, servers)

        # Find the relaxed solution
        relaxed_result = relaxed_algorithm(tasks, servers, relaxed_time_limit)
        algorithm_results[relaxed_result.algorithm_name] = relaxed_result.store() \
            if relaxed_result is not None else 'failure'
        reset_model(tasks, servers)

        # Loop over all of the greedy policies permutations
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(tasks, servers, value_density, server_selection_policy,
                                                     resource_allocation_policy)
                    algorithm_results[greedy_result.algorithm_name] = greedy_result.store()
                    reset_model(tasks, servers)

        # Loop over all of the matrix policies
        for policy in matrix_policies:
            greedy_matrix_result = matrix_greedy(tasks, servers, policy)
            algorithm_results[greedy_matrix_result.algorithm_name] = greedy_matrix_result.store()
            reset_model(tasks, servers)

        # Add the results to the data
        data.append(algorithm_results)

    # Save the results to the file
    filename = results_filename('optimal_greedy_test', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print(f'Successful, data saved to {filename}')


def all_policies_test(model_dist: ModelDistribution, repeat: int, repeats: int = 200):
    """
    All policies test

    :param model_dist: The model distributions
    :param repeat: The repeat
    :param repeats: The number of repeats
    """
    print(f'Greedy test of all policies for {model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    data = []

    # Loop, for each run all of the algorithms
    for _ in tqdm(range(repeats)):
        # Generate the tasks and the servers
        tasks, servers = model_dist.create()
        algorithm_results = {}

        # Loop over all of the greedy policies permutations
        for value_density in all_value_densities:
            for server_selection_policy in all_server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(tasks, servers, value_density, server_selection_policy,
                                                     resource_allocation_policy)
                    algorithm_results[greedy_result.algorithm_name] = greedy_result.store()
                    print(f'{greedy_result.algorithm_name} -> {greedy_result.store()}')
                    reset_model(tasks, servers)

        # Add the results to the data
        data.append(algorithm_results)

    # Save the results to the file
    filename = results_filename('all_greedy_test', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print(f'Successful, data saved to {filename}')


def allocation_test(model_dist: ModelDistribution, repeat: int, repeats: int = 50,
                    optimal_time_limit: int = 300, relaxed_time_limit: int = 150):
    """
    Allocation test

    :param model_dist: The model distribution
    :param repeat: The repeat number
    :param repeats: The number of repeats
    :param optimal_time_limit: The optimal time limit
    :param relaxed_time_limit: The relaxed time limit
    """

    def task_data() -> Dict[str, Tuple[int, int, int, str]]:
        """
        Generate the important task data

        :return: The dictionary of task data
        """
        return {
            task.name: (task.loading_speed, task.compute_speed, task.sending_speed, task.running_server.name)
            for task in tasks if task.running_server
        }

    def model_data():
        """
        Generate the json for saving the model data usd

        :return: The json for the
        """
        return (
            {task.name: (task.required_storage, task.required_computation, task.required_results_data,
                         task.deadline, task.value) for task in tasks},
            {server.name: (server.storage_capacity, server.computation_capacity, server.bandwidth_capacity)
             for server in servers}
        )

    print(f'Allocation testing using the results of the greedy, relaxed and optimal {model_dist.num_tasks} tasks and '
          f'{model_dist.num_servers} servers')
    data = []

    # Loop, for each run all of the algorithms
    for _ in tqdm(range(repeats)):
        # Generate the tasks and the servers
        tasks, servers = model_dist.create()
        algorithm_results = {'model': model_data()}

        # Find the optimal solution
        optimal_result = optimal_algorithm(tasks, servers, optimal_time_limit)
        algorithm_results[optimal_result.algorithm_name] = optimal_result.store(tasks_data=task_data()) \
            if optimal_result is not None else 'failure'
        reset_model(tasks, servers)

        # Find the relaxed solution
        relaxed_result = relaxed_algorithm(tasks, servers, relaxed_time_limit)
        algorithm_results[relaxed_result.algorithm_name] = relaxed_result.store(tasks_data=task_data()) \
            if relaxed_result is not None else 'failure'
        reset_model(tasks, servers)

        # Loop over all of the greedy policies permutations
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(tasks, servers, value_density, server_selection_policy,
                                                     resource_allocation_policy)
                    algorithm_results[greedy_result.algorithm_name] = greedy_result.store(tasks_data=task_data())
                    reset_model(tasks, servers)

        # Loop over all of the matrix policies
        for policy in matrix_policies:
            greedy_matrix_result = matrix_greedy(tasks, servers, policy)
            algorithm_results[greedy_matrix_result.algorithm_name] = greedy_matrix_result.store(tasks_data=task_data())
            reset_model(tasks, servers)

        # Add the results to the data
        data.append(algorithm_results)

    # Save the results to the file
    filename = results_filename('optimal_greedy_test', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print(f'Successful, data saved to {filename}')


def paper_testing(model_dist: ModelDistribution, repeat: int, repeats: int = 100, debug_results: bool = False):
    """
    Testing to be used in the paper

    :param model_dist: Model distribution
    :param repeat: The repeat
    :param repeats: The number of repeats
    :param debug_results: If to debug the results
    """
    print(f'Greedy testing with optimal, fixed and relaxed for {model_dist.num_tasks} tasks and ' 
          f'{model_dist.num_servers} servers')
    data = []
    for _ in tqdm(range(repeats)):
        tasks, servers = model_dist.create()
        results = {}

        # Optimal
        optimal_result = branch_bound_algorithm(tasks, servers)
        results['Optimal'] = optimal_result.store() if optimal_result else 'failure'
        if debug_results:
            print(results['Optimal'])

        reset_model(tasks, servers)

        # Fixed Optimal
        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]
        fixed_result = branch_bound_algorithm(fixed_tasks, servers, feasibility=fixed_feasible_allocation)
        results['Fixed'] = fixed_result.store() if fixed_result else 'failure'
        if debug_results:
            print(results['Fixed'])

        reset_model(fixed_tasks, servers)

        # Relaxed solution
        relaxed_result = branch_bound_algorithm(tasks, [SuperServer(servers)])
        results['Relaxed'] = relaxed_result.store() if relaxed_result else 'failure'
        if debug_results:
            print(results['Relaxed'])

        reset_model(tasks, servers)

        greedy_policies = [
            (vd, ss, ra)
            for vd in [UtilityPerResources(), UtilityResourcePerDeadline(), UtilityDeadlinePerResource(), Value()]
            for ss in [SumResources(), SumResources(True),
                       TaskSumResources(SumPercentage()), TaskSumResources(SumPercentage(), True),
                       TaskSumResources(SumSpeed()), TaskSumResources(SumSpeed(), True)]
            for ra in [SumPercentage(), SumSpeed()]
        ]
        for (vd, ss, ra) in greedy_policies:
            try:
                greedy_result = greedy_algorithm(tasks, servers, vd, ss, ra)
                results[greedy_result.algorithm_name] = greedy_result.store()

                if debug_results:
                    print(results[greedy_result.algorithm_name])
            except Exception as e:
                print(e)

            reset_model(tasks, servers)

        reset_model(tasks, servers)
        greedy_result = greedy_algorithm(tasks, servers, RandomValueDensity(), RandomServerSelection(), SumPercentage())
        results[greedy_result.algorithm_name] = greedy_result.store()

        reset_model(tasks, servers)
        greedy_result = greedy_algorithm(tasks, servers, RandomValueDensity(), RandomServerSelection(), SumSpeed())
        results[greedy_result.algorithm_name] = greedy_result.store()

        data.append(results)
        print(results)

        # Save the results to the file
        filename = results_filename('flexible_greedy', model_dist.file_name, repeat)
        with open(filename, 'w') as file:
            json.dump(data, file)


if __name__ == "__main__":
    args = load_args()

    model_name, task_dist, server_dist = load_model_distribution(args['model'])
    loaded_model_dist = ModelDistribution(model_name, task_dist, args['tasks'], server_dist, args['servers'])

    # best_algorithms_test(loaded_model_dist, args['repeat'])
    # allocation_test(loaded_model_dist, args['repeat'])
    # all_policies_test(loaded_model_dist, args['repeat'], repeats=1)
    paper_testing(loaded_model_dist, args['repeat'], repeats=25)
