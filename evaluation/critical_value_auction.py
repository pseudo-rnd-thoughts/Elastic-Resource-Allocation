"""Critical Value testing"""

from __future__ import annotations

import json

from tqdm import tqdm

from auctions.critical_value_auction import critical_value_auction
from auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction
from auctions.vcg_auction import vcg_auction, fixed_vcg_auction
from core.core import reset_model
from core.fixed_task import FixedTask, FixedSumSpeeds
from core.io import load_args
from greedy.resource_allocation_policy import SumPercentage, SumSpeed
from greedy.resource_allocation_policy import policies as resource_allocation_policies
from greedy.server_selection_policy import SumResources, TaskSumResources
from greedy.server_selection_policy import policies as server_selection_policies
from greedy.value_density import UtilityPerResources, UtilityResourcePerDeadline, UtilityDeadlinePerResource, Value
from greedy.value_density import policies as value_densities
from model.model_distribution import ModelDistribution, load_model_distribution, results_filename


def critical_value_testing(model_dist: ModelDistribution, repeat: int, repeats: int = 50, price_change: int = 3,
                           vcg_time_limit: int = 15, fixed_vcg_time_limit: int = 15,
                           decentralised_iterative_time_limit: int = 15):
    """
    The critical value testing
    :param model_dist: The model distribution
    :param repeat: The repeat
    :param repeats: The number of repeats
    :param price_change: The price change
    :param vcg_time_limit:
    :param fixed_vcg_time_limit:
    :param decentralised_iterative_time_limit: The decentralised iterative time limit
    """
    print(f'Critical Value testing for {model_dist.num_tasks} tasks and {model_dist.num_servers} servers')

    data = []

    # Loop, for each run all of the auctions to find out the results from each type
    for _ in tqdm(range(repeats)):
        # Generate the tasks and servers
        tasks, servers = model_dist.create()
        auction_results = {}

        # Calculate the vcg auction
        vcg_result = vcg_auction(tasks, servers)
        auction_results['vcg'] = vcg_result.store() if vcg_result is not None else 'failure'
        reset_model(tasks, servers)

        # Calculate the fixed vcg auction
        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]
        fixed_vcg_result = fixed_vcg_auction(fixed_tasks, servers)
        auction_results['fixed vcg'] = fixed_vcg_result.store() if fixed_vcg_result is not None else 'failure'
        reset_model(tasks, servers)

        # The decentralised iterative auction results
        for server in servers:
            server.price_change = price_change
        iterative_result = optimal_decentralised_iterative_auction(tasks, servers, decentralised_iterative_time_limit)
        auction_results[f'price change {price_change}'] = iterative_result.store()
        reset_model(tasks, servers)

        # Tests the critical value
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    try:
                        critical_value_result = critical_value_auction(tasks, servers, value_density,
                                                                       server_selection_policy,
                                                                       resource_allocation_policy)
                        auction_results[critical_value_result.algorithm] = critical_value_result.store()
                    except Exception as e:
                        print('Critical Error', e)

                    reset_model(tasks, servers)

        # Append the auction results to the data
        data.append(auction_results)

    # Save all of the results to a file
    filename = results_filename('critical_values_results', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print(f'Successful, data saved to {filename}')


def all_policies_critical_value(model_dist: ModelDistribution, repeat: int, repeats: int = 50,
                                vcg_time_limit: int = 60, fixed_vcg_time_limit: int = 60):
    """
    All policies test for critical value

    :param model_dist: The model dist
    :param repeat: The repeat
    :param repeats: The number of repeats
    :param vcg_time_limit: The VCG time limit
    :param fixed_vcg_time_limit: THe Fixed VCG time limit
    """
    print(f'Critical value test of all policies for {model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    data = []

    # Loop, for each run all of the algorithms
    for _ in tqdm(range(repeats)):
        # Generate the tasks and the servers
        tasks, servers = model_dist.create()
        auction_results = {}

        # Calculate the vcg auction
        vcg_result = vcg_auction(tasks, servers)
        auction_results['vcg'] = vcg_result.store() if vcg_result is not None else 'failure'
        reset_model(tasks, servers)

        # Calculate the fixed vcg auction
        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]
        fixed_vcg_result = fixed_vcg_auction(fixed_tasks, servers)
        auction_results['fixed vcg'] = fixed_vcg_result.store() if fixed_vcg_result is not None else 'failure'
        reset_model(tasks, servers)

        # Loop over all of the greedy policies permutations
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    critical_value_result = critical_value_auction(tasks, servers, value_density,
                                                                   server_selection_policy, resource_allocation_policy)
                    auction_results[critical_value_result.algorithm] = critical_value_result.store()
                    reset_model(tasks, servers)

        # Add the results to the data
        data.append(auction_results)

    # Save the results to the file
    filename = results_filename('all_critical_value_test', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print(f'Successful, data saved to {filename}')


def auction_testing(model_dist: ModelDistribution, repeat: int, repeats: int = 100, vcg_time_limit: int = 15,
                    debug_results: bool = False):
    """
    Critical value auction testing

    :param model_dist: The model distribution
    :param repeat: The repeat number
    :param repeats: The number of repeats
    :param vcg_time_limit: The VCG time limit
    :param debug_results: If to debug the results
    """
    print(f'Auction testing with optimal, fixed and relaxed for {model_dist.num_tasks} tasks and '
          f'{model_dist.num_servers} servers')
    data = []
    for _ in tqdm(range(repeats)):
        tasks, servers = model_dist.create()
        results = {}

        vcg_result = vcg_auction(tasks, servers)
        results['VCG'] = vcg_result.store() if vcg_result else 'failure'
        if debug_results:
            print(results['VCG'])

        reset_model(tasks, servers)

        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]
        fixed_result = fixed_vcg_auction(fixed_tasks, servers)
        results['Fixed VCG'] = fixed_result.store() if fixed_result else 'failure'
        if debug_results:
            print(results['Fixed VCG'])

        reset_model(fixed_tasks, servers)

        critical_value_policies = [
            (vd, ss, ra)
            for vd in [UtilityPerResources(), UtilityResourcePerDeadline(), UtilityDeadlinePerResource(), Value()]
            for ss in [SumResources(), SumResources(True),
                       TaskSumResources(SumPercentage()), TaskSumResources(SumPercentage(), True),
                       TaskSumResources(SumSpeed()), TaskSumResources(SumSpeed(), True)]
            for ra in [SumPercentage(), SumSpeed()]
        ]
        for (vd, ss, ra) in critical_value_policies:
            critical_value_result = critical_value_auction(tasks, servers, vd, ss, ra)
            results[critical_value_result.algorithm] = critical_value_result.store()
            if debug_results:
                print(results[critical_value_result.algorithm])

            reset_model(tasks, servers)

        data.append(results)
        print(results)

        # Save the results to the file
        filename = results_filename('flexible_auction', model_dist.file_name, repeat)
        with open(filename, 'w') as file:
            json.dump(data, file)


if __name__ == "__main__":
    args = load_args()

    model_name, task_dist, server_dist = load_model_distribution(args['model'])
    loaded_model_dist = ModelDistribution(model_name, task_dist, args['tasks'], server_dist, args['servers'])

    # critical_value_testing(loaded_model_dist, args['repeat'])
    # all_policies_critical_value(loaded_model_dist, args['repeat'])
    auction_testing(loaded_model_dist, args['repeat'])
