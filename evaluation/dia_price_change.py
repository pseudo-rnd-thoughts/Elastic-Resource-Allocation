"""Optimality Testing"""

from __future__ import annotations

import json
from random import gauss
from typing import Iterable

from tqdm import tqdm

from auctions.critical_value_auction import critical_value_auction
from auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction
from auctions.vcg_auction import fixed_vcg_auction
from auctions.vcg_auction import vcg_auction
from core.core import set_price_change, reset_model
from core.fixed_task import FixedTask, FixedSumSpeeds
from extra.io import load_args
from greedy.resource_allocation_policy import SumPercentage, SumSpeed
from greedy.server_selection_policy import SumResources, TaskSumResources
from greedy.value_density import UtilityPerResources, UtilityResourcePerDeadline, UtilityDeadlinePerResource, Value
from extra.model import ModelDistribution, results_filename


def uniform_price_change_test(model_dist: ModelDistribution, repeat: int, repeats: int = 50,
                              price_changes: Iterable[int] = (1, 2, 3, 5, 7, 10), initial_cost: int = 15,
                              vcg_time_limit: int = 15, time_limit: int = 15, debug_results: bool = False):
    """
    Test the decentralised iterative auction where a uniform price change

    :param model_dist: The model distribution
    :param repeat: The repeat number
    :param repeats: The number of repeats
    :param price_changes: The uniform price changes
    :param initial_cost: The initial cost of the task
    :param vcg_time_limit: The compute time limit for vcg
    :param time_limit: The compute time limit for decentralised iterative time limit
    :param debug_results:
    """
    print(f"Single price change of {', '.join([str(x) for x in price_changes])} with iterative auctions for "
          f"{model_dist.num_tasks} tasks and {model_dist.num_servers} servers")

    data = []

    # Loop, for each run all of the auctions to find out the results from each type
    for _ in tqdm(range(repeats)):
        # Generate the tasks and servers
        tasks, servers = model_dist.generate()
        auction_results = {}

        # Calculate the vcg auction
        vcg_result = vcg_auction(tasks, servers, vcg_time_limit)
        auction_results['vcg'] = vcg_result.store() if vcg_result is not None else 'failure'
        if debug_results:
            print(auction_results['vcg'])

        reset_model(tasks, servers)

        # Calculate the fixed vcg auction
        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]
        fixed_vcg_result = fixed_vcg_auction(fixed_tasks, servers)
        auction_results['fixed vcg'] = fixed_vcg_result.store() if fixed_vcg_result is not None else 'failure'
        if debug_results:
            print(auction_results['fixed vcg'])

        # For each uniform price change, set all of the server prices to that and solve auction
        for price_change in price_changes:
            reset_model(tasks, servers)

            set_price_change(servers, price_change)
            iterative_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit)
            auction_results[f'price change {price_change}'] = iterative_result.store()
            if debug_results:
                print(auction_results[f'price change {price_change}'])

        reset_model(tasks, servers)

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
            auction_results[critical_value_result.algorithm] = critical_value_result.store()
            if debug_results:
                print(auction_results[critical_value_result.algorithm])

            reset_model(tasks, servers)
        # Append the auction results to the data
        data.append(auction_results)
        print(auction_results)

        # Save all of the results to a file
        filename = results_filename('price_change_auction', model_dist, repeat)
        with open(filename, 'w') as file:
            json.dump(data, file)


def non_uniform_price_change_test(model_dist: ModelDistribution, repeat: int, price_changes: int = 10,
                                  repeats: int = 20,
                                  vcg_time_limit: int = 15, fixed_vcg_time_limit: int = 15, dia_time_limit: int = 15,
                                  price_change_mean: int = 2, price_change_std: int = 4):
    """
    Test non uniform price change servers on the decentralised iterative auction

    :param model_dist: The model distribution
    :param repeat: The repeat number
    :param price_changes: The number of price changes
    :param repeats: The number of repeats
    :param vcg_time_limit: The vcg compute time limit
    :param fixed_vcg_time_limit: The fixed vcg compute time limit
    :param dia_time_limit: The decentralised iterative compute time limit
    :param price_change_mean: The price change mean value
    :param price_change_std: The price change standard deviation
    """
    print(f'Multiple price change with iterative auctions for '
          f'{model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    data = []

    # Generate all of the price changes
    prices_changes = [[max(1, int(abs(gauss(price_change_mean, price_change_std))))
                       for _ in range(model_dist.num_servers)] for _ in range(price_changes)]

    # Loop, for each calculate the result for the results
    for _ in tqdm(range(repeats)):
        tasks, servers = model_dist.generate()
        auction_results = {}

        # Calculate the fixed vcg auction
        vcg_result = vcg_auction(tasks, servers, vcg_time_limit)
        auction_results['vcg'] = vcg_result.store() if vcg_result is not None else 'failure'
        reset_model(tasks, servers)

        # Calculate the fixed vcg auction
        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]
        fixed_vcg_result = fixed_vcg_auction(fixed_tasks, servers, fixed_vcg_time_limit)
        auction_results['fixed vcg'] = fixed_vcg_result.store() if fixed_vcg_result is not None else 'failure'

        for price_changes in prices_changes:
            reset_model(tasks, servers)
            for server, price_change in zip(servers, price_changes):
                server.price_change = price_change

            iterative_results = optimal_decentralised_iterative_auction(tasks, servers, dia_time_limit)
            name = f'price change: {", ".join([str(x) for x in price_changes])}'
            auction_results[name] = iterative_results.store()

        # Append the auction results to the data
        data.append(auction_results)
        print(auction_results)

        # Save the results to a file
        filename = results_filename('non_uniform_price_change_auction_results', model_dist, repeat)
        with open(filename, 'w') as file:
            json.dump(data, file)


if __name__ == "__main__":
    args = load_args()
    loaded_model_dist = ModelDistribution(args['model'], args['tasks'], args['servers'])

    uniform_price_change_test(loaded_model_dist, args['repeat'], time_limit=5)
    # non_uniform_price_change_test(loaded_model_dist, args['repeat'])
