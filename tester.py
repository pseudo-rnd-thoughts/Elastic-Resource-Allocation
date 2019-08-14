"""Tester of the greedy algorithm"""

from __future__ import annotations
from typing import List, Dict

import core.graphing as graphing
from core.job import Job
from core.model import load_dist, reset_model, ModelDist
from core.result import Result, AlgorithmResults, print_repeat_results
from core.server import Server
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import policies as resource_allocation_policies, ResourceAllocationPolicy, SumSpeeds
from greedy.server_selection_policy import policies as server_selection_policies, ServerSelectionPolicy, SumResources
from greedy.value_density import policies as value_densities, ValueDensity, UtilityPerResources
from optimal.optimal import optimal_algorithm


def greedy_test(jobs: List[Job], servers: List[Server], value_density: ValueDensity,
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


def optimal_test(jobs: List[Job], servers: List[Server]):
    """
    Test for the optimal algorithm solution
    :param jobs: A list of jobs
    :param servers: A list of servers
    """
    result = optimal_algorithm(jobs, servers)
    #result.print(servers)


def multi_policy_test(jobs: List[Job], servers: List[Server], _value_densities: List[ValueDensity],
                      _server_allocation_policies: List[ServerSelectionPolicy],
                      _resource_allocation_policies: List[ResourceAllocationPolicy],
                      run_optimal_algorithm: bool = False, plot_results: bool = True,
                      algorithm_result_debug: bool = False) -> List[Result]:
    """
    Runs through a multi policy greedy algorithm test that loops through all of the policy permutations to test with
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param _value_densities: A list of value density classes
    :param _server_allocation_policies: A list of server allocation policy classes
    :param _resource_allocation_policies: A list of resource allocation policy classes
    :param run_optimal_algorithm: Runs the optimal algorithm as well
    :param plot_results: If to plot the results
    :param algorithm_result_debug: If to print the algorithm results
    :return: A list of results
    """
    results: List[Result] = []
    for value_density in _value_densities:
        for server_allocation_policy in _server_allocation_policies:
            for resource_allocation_policy in _resource_allocation_policies:
                result = greedy_algorithm(jobs, servers,
                                          value_density, server_allocation_policy, resource_allocation_policy)
                if algorithm_result_debug:
                    result.print(servers)

                results.append(result)
                reset_model(jobs, servers)

    if run_optimal_algorithm:
        results.append(optimal_algorithm(jobs, servers))
    if plot_results:
        graphing.plot_algorithms_results(results)
    return results


def repeat_test(model_generator: ModelDist, _value_densities: List[ValueDensity],
                _server_allocation_policies: List[ServerSelectionPolicy],
                _resource_allocation_policies: List[ResourceAllocationPolicy],
                num_repeats=5, run_optimal_algorithm: bool = False, plot_repeat_results: bool = True,
                debug_repeat_results: bool = False) -> List[AlgorithmResults]:
    """
    Repeats greedy test
    :param model_generator: A model generator function
    :param _value_densities: A list of value density functions
    :param _server_allocation_policies: A list of server allocation policies
    :param _resource_allocation_policies: A list of resource allocation policies
    :param num_repeats: A num of model repeats
    :param run_optimal_algorithm: To run the optimal algorithm
    :param plot_repeat_results: To plot repeat results
    :param debug_repeat_results: To debug the repeat results
    """
    model_repeat_results: List[List[Result]] = []
    for repeat in range(num_repeats):
        jobs, servers = model_generator.create()
        model_results = multi_policy_test(jobs, servers, _value_densities, _server_allocation_policies,
                                          _resource_allocation_policies,
                                          run_optimal_algorithm=run_optimal_algorithm, plot_results=False)
        model_repeat_results.append(model_results)

    algorithm_results = [
        AlgorithmResults([model_repeat_results[repeat][algorithm] for repeat in range(num_repeats)])
        for algorithm in range(len(model_repeat_results[0]))
    ]

    if debug_repeat_results:
        print_repeat_results(algorithm_results)
    if plot_repeat_results:
        graphing.plot_repeat_algorithm_results(algorithm_results)

    return algorithm_results


def multi_model_test(model_generators: List[ModelDist], _value_densities: List[ValueDensity],
                     _server_allocation_policies: List[ServerSelectionPolicy],
                     _resource_allocation_policies: List[ResourceAllocationPolicy],
                     num_repeats=5, run_optimal_algorithm: bool = False):
    """
    Multiple model test
    :param model_generators: A list of model generators
    :param _value_densities:
    :param _server_allocation_policies:
    :param _resource_allocation_policies:
    :param num_repeats:
    :param run_optimal_algorithm:
    :return:
    """
    model_algorithm_tests: Dict[str, List[AlgorithmResults]] = {}
    for model_generator in model_generators:
        model_algorithm_tests[model_generator.name] = repeat_test(model_generator, _value_densities,
                                                                  _server_allocation_policies,
                                                                  _resource_allocation_policies,
                                                                  num_repeats=num_repeats,
                                                                  run_optimal_algorithm=run_optimal_algorithm,
                                                                  plot_repeat_results=False)

    graphing.plot_multi_models_results(model_algorithm_tests)


if __name__ == "__main__":
    basic_dist_name, basic_job_dist, basic_server_dist = load_dist("../models/basic.model")
    basic_model_dist = ModelDist(basic_dist_name, basic_job_dist, 15, basic_server_dist, 3)

    _jobs, _servers = basic_model_dist.create()
    print("Plot the jobs and servers")
    graphing.plot_jobs(_jobs)
    graphing.plot_servers(_servers)
    print("Testing the greedy algorithm")
    greedy_test(_jobs, _servers, UtilityPerResources(), SumResources(), SumSpeeds())
    graphing.plot_server_jobs_allocations(_servers)

    reset_model(_jobs, _servers)
    print("Testing the optimal algorithm")
    optimal_test(_jobs, _servers)
    graphing.plot_server_jobs_allocations(_servers)

    print("Multi Policy Greedy test")
    _jobs, _servers = basic_model_dist.create()
    multi_policy_test(_jobs, _servers, value_densities, server_selection_policies, resource_allocation_policies,
                      run_optimal_algorithm=True)

    print("Repeat Greed Test")
    repeat_test(basic_model_dist, value_densities, server_selection_policies,
                resource_allocation_policies, run_optimal_algorithm=True)

    print("Multi Model testing")
    bs_dist_name, bs_job_dist, bs_server_dist = load_dist("../models/big_small.model")
    multi_model_test([ModelDist(bs_dist_name, bs_job_dist, num_jobs, bs_server_dist, num_servers)
                      for num_jobs, num_servers in ((11, 2), (15, 3), (25, 4), (35, 5))],
                     value_densities, server_selection_policies, resource_allocation_policies,
                     run_optimal_algorithm=True)
