"""Iterative Round testing"""

from __future__ import annotations

import json
from typing import List

from tqdm import tqdm

from auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction
from core.core import set_price_change, reset_model
from core.io import load_args
from model.model_distribution import ModelDistribution, load_model_distribution, results_filename


def round_test(model_dist: ModelDistribution, repeat: int, initial_costs: List[int], price_changes: List[int],
               repeats: int = 50, time_limit: int = 15):
    """
    Round test

    :param model_dist: The model distribution
    :param repeat: The repeat
    :param initial_costs: The initial cost functions
    :param price_changes: The price changes
    :param repeats: The number of repeats
    :param time_limit: The time limit to solve with
    """
    data = []

    for _ in tqdm(range(repeats)):
        tasks, servers = model_dist.create()
        auction_results = {}

        for initial_cost in initial_costs:
            for price_change in price_changes:
                for server in servers:
                    server.price_change = price_change

                results = optimal_decentralised_iterative_auction(tasks, servers, time_limit)
                if results is not None:
                    auction_results[f'cost {initial_cost}, change {price_change}'] = \
                        results.store(initial_cost=initial_cost, price_change=price_change)
                reset_model(tasks, servers)

        data.append(auction_results)

        # Save all of the results to a file
        filename = results_filename('iterative_round_results', model_dist.file_name, repeat)
        with open(filename, 'w') as file:
            json.dump(data, file)


def round_num_testing(model_dist: ModelDistribution, repeat: int, repeats: int = 50, time_limit: int = 15,
                      debug_results: bool = False):
    """
    Testing the number of rounds required to convergence on the price

    :param model_dist: The model distribution
    :param repeat: The repeat number
    :param repeats: The number of repeats
    :param time_limit: The time limit for the auctions
    :param debug_results: If to debug the results
    """
    print(f'Round Num testing for {model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    data = []
    initial_costs = [0, 5, 10, 15, 20]
    price_changes = [1, 2,  5,  8, 10]
    
    for _ in tqdm(range(repeats)):
        tasks, servers = model_dist.create()

        results = {}

        for initial_cost in initial_costs:
            for price_change in price_changes:
                set_price_change(servers, price_change)

                name = f'Initial Cost {initial_cost} Price Change {price_change}'
                result = optimal_decentralised_iterative_auction(tasks, servers, time_limit)
                results[name] = result.store(price_change=price_change)
                
                if debug_results:
                    print(results[name])

                reset_model(tasks, servers)

        data.append(results)
        print(results)

    # Save the results to the file
    filename = results_filename('round_num', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print(f'Successful, data saved to {filename}')


if __name__ == "__main__":
    args = load_args()

    model_name, task_dist, server_dist = load_model_distribution(args['model'])
    loaded_model_dist = ModelDistribution(model_name, task_dist, args['tasks'], server_dist, args['servers'])

    round_num_testing(loaded_model_dist, args['repeat'], time_limit=5)
