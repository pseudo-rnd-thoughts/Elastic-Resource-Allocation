"""Greedy Testing"""

from __future__ import annotations
from typing import List, Dict

from tqdm import tqdm

from core.job import Job
from core.server import Server
from core.result import Result, AlgorithmResults, print_repeat_results
from core.model import ModelDist, reset_model

import core.graphing as graphing

from optimal.optimal import optimal_algorithm

from greedy.greedy import greedy_algorithm
from greedy_matrix.matrix_greedy import matrix_greedy
from greedy.resource_allocation_policy import ResourceAllocationPolicy
from greedy.server_selection_policy import ServerSelectionPolicy
from greedy.value_density import ValueDensity

from greedy.resource_allocation_policy import SumSpeeds as BestResourceAllocation
from greedy.value_density import UtilityDeadlinePerResource as BestValueDensity
from greedy.server_selection_policy import SumResources as BestServerSelection
from greedy_matrix.matrix_policy import SumServerUsage as BestMatrixPolicy

from greedy_matrix.matrix_policy import policies as matrix_policies


def run_greedy(jobs: List[Job], servers: List[Server], value_density: ValueDensity,
               server_selection_policy: ServerSelectionPolicy, resource_allocation_policy: ResourceAllocationPolicy):
    """
    A basic test with a supplied value density, selection policy and bid policy functions
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param value_density: The value density function
    :param server_selection_policy: The selection policy function
    :param resource_allocation_policy: The resource allocation function
    """
    result: Result = greedy_algorithm(jobs, servers, value_density, server_selection_policy, resource_allocation_policy,
                                      job_values_debug=True)
    result.print(servers)


def run_matrix_greedy(dist: ModelDist, repeat=100):
    data = []
    
    while len(data) < 3 * repeat:
        jobs, servers = dist.create()
        
        optimal_result = optimal_algorithm(jobs, servers)
        if optimal_result is None:
            continue
        optimal_utility = optimal_result.total_utility
        data.append(['optimal', optimal_utility, 0])
        reset_model(jobs, servers)
        
        for matrix_policy in matrix_policies:
            matrix_result = matrix_greedy(jobs, servers, matrix_policy)
            matrix_utility = matrix_result.total_utility
            matrix_difference = optimal_utility - matrix_utility
            data.append([matrix_policy.name + 'matrix', matrix_utility, matrix_difference])
            reset_model(jobs, servers)
        
        greedy_result = greedy_algorithm(jobs, servers, BestValueDensity(), BestServerSelection(),
                                         BestResourceAllocation())
        greedy_utility = greedy_result.total_utility
        greedy_difference = optimal_utility - greedy_utility
        data.append(['greedy', greedy_utility, greedy_difference])


def greedy_multi_policy(jobs: List[Job], servers: List[Server], _value_densities: List[ValueDensity],
                        _server_selection_policies: List[ServerSelectionPolicy],
                        _resource_allocation_policies: List[ResourceAllocationPolicy],
                        run_optimal_algorithm: bool = False, run_matrix_greedy_algorithm: bool = False,
                        plot_results: bool = True, algorithm_result_debug: bool = False) -> List[Result]:
    """
    Runs through a multi policy greedy algorithm test that loops through all of the policy permutations to test with
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param _value_densities: A list of value density classes
    :param _server_selection_policies: A list of server allocation policy classes
    :param _resource_allocation_policies: A list of resource allocation policy classes
    :param run_optimal_algorithm: Runs the optimal algorithm
    :param run_matrix_greedy_algorithm: Run the matrix greedy algorithm
    :param plot_results: If to plot the results
    :param algorithm_result_debug: If to print the algorithm results
    :return: A list of results
    """
    results: List[Result] = []
    for value_density in _value_densities:
        for server_selection_policy in _server_selection_policies:
            for resource_allocation_policy in _resource_allocation_policies:
                result = greedy_algorithm(jobs, servers,
                                          value_density, server_selection_policy, resource_allocation_policy)
                if algorithm_result_debug:
                    result.print(servers)
                
                results.append(result)
                reset_model(jobs, servers)
    
    if run_optimal_algorithm:
        results.append(optimal_algorithm(jobs, servers))
    if run_matrix_greedy_algorithm:
        results.append(matrix_greedy(jobs, servers, BestMatrixPolicy()))
    if plot_results:
        graphing.plot_algorithms_results(results)
    return results


def repeat_greedy(model_generator: ModelDist, _value_densities: List[ValueDensity],
                  _server_selection_policies: List[ServerSelectionPolicy],
                  _resource_allocation_policies: List[ResourceAllocationPolicy],
                  num_repeats: int = 5, run_optimal_algorithm: bool = False, plot_repeat_results: bool = True,
                  debug_repeat_results: bool = False) -> List[AlgorithmResults]:
    """
    Repeats greedy test
    :param model_generator: A model generator function
    :param _value_densities: A list of value density functions
    :param _server_selection_policies: A list of server allocation policies
    :param _resource_allocation_policies: A list of resource allocation policies
    :param num_repeats: A num of model repeats
    :param run_optimal_algorithm: To run the optimal algorithm
    :param plot_repeat_results: To plot repeat results
    :param debug_repeat_results: To debug the repeat results
    """
    model_repeat_results: List[List[Result]] = []
    for _ in tqdm(range(num_repeats)):
        jobs, servers = model_generator.create()
        model_results = greedy_multi_policy(jobs, servers, _value_densities, _server_selection_policies,
                                            _resource_allocation_policies,
                                            run_optimal_algorithm=run_optimal_algorithm, plot_results=False)
        model_repeat_results.append(model_results)
    
    algorithm_results = [
        AlgorithmResults([model_repeat_results[repeat][algorithm] for repeat in range(num_repeats)],
                         model_repeat_results[-1])
        for algorithm in range(len(model_repeat_results[0]))
    ]
    
    if debug_repeat_results:
        print_repeat_results(algorithm_results)
    if plot_repeat_results:
        graphing.plot_repeat_algorithm_results(algorithm_results)
    
    return algorithm_results


def greedy_multi_model(model_generators: List[ModelDist], _value_densities: List[ValueDensity],
                       _server_selection_policies: List[ServerSelectionPolicy],
                       _resource_allocation_policies: List[ResourceAllocationPolicy],
                       num_repeats=5, run_optimal_algorithm: bool = False):
    """
    Multiple model test
    :param model_generators: A list of model generators
    :param _value_densities: A list of value densities
    :param _server_selection_policies: A list of server selection policies
    :param _resource_allocation_policies: A list of resource allocation policies
    :param num_repeats: The number of model repeats
    :param run_optimal_algorithm: If to run the optimal algorithm as well
    """
    model_algorithm_tests: Dict[str, List[AlgorithmResults]] = {}
    for model_generator in model_generators:
        model_algorithm_tests[model_generator.name] = repeat_greedy(model_generator, _value_densities,
                                                                    _server_selection_policies,
                                                                    _resource_allocation_policies,
                                                                    num_repeats=num_repeats,
                                                                    run_optimal_algorithm=run_optimal_algorithm,
                                                                    plot_repeat_results=False)
    
    graphing.plot_multi_models_results(model_algorithm_tests)
