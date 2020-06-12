"""Iterative Round testing"""

from __future__ import annotations

import json
from typing import List, Callable

from tqdm import tqdm

from auctions.decentralised_iterative_auction import decentralised_iterative_auction
from src.core.core import results_filename, load_args
from src.core.task import Task
from src.core.model import ModelDist, load_dist, reset_model


def round_test(model_dist: ModelDist, repeat: int, initial_costs: List[Callable[[Task], int]],
               price_changes: List[int], repeats: int = 50, time_limit: int = 15):
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

                results = decentralised_iterative_auction(tasks, servers, time_limit, initial_cost=initial_cost)
                if results is not None:
                    auction_results[f'cost {initial_cost(tasks[0])}, change {price_change}'] = \
                        results.store(initial_cost=initial_cost(tasks[0]), price_change=price_change)
                reset_model(tasks, servers)

        data.append(auction_results)

    # Save all of the results to a file
    filename = results_filename('iterative_round_results', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print(f'Successful, data saved to {filename}')


def basic_test(model_dist: ModelDist):
    """
    Basic test for iterative round testing

    :param model_dist: Model distribution
    """
    tasks, servers = model_dist.create()

    price_change = 1
    for server in servers:
        server.price_change = price_change
    results = decentralised_iterative_auction(tasks, servers, 15, initial_cost=lambda task: 1,
                                              debug_allocation=True, debug_results=True)
    print(results.data)


if __name__ == "__main__":
    args = load_args()

    model_name, task_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, task_dist, args['tasks'], server_dist, args['servers'])


    def cost_lambda(cost: int) -> Callable[[Task], int]:
        """
        Create a lambda function for the cost
        
        :param cost: The fixed cost
        :return: lambda function
        """
        return lambda task: cost


    task_initial_cost = [
        cost_lambda(cost) for cost in range(0, int(sum(dist.value_mean for dist in task_dist) / len(task_dist)), 10)
    ]
    server_price_changes = [1, 2, 5, 10, 15]

    # round_test(loaded_model_dist, args['repeat'], task_initial_cost, server_price_changes)
    basic_test(loaded_model_dist)
