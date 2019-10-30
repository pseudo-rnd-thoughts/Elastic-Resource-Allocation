"""Iterative Round testing"""

from __future__ import annotations

from typing import List, Callable
import json

from tqdm import tqdm

from core.core import results_filename, load_args
from core.job import Job
from core.model import ModelDist, load_dist, reset_model
from auctions.decentralised_iterative_auction import decentralised_iterative_auction


def round_test(model_dist: ModelDist, repeat: int, initial_costs: List[int], price_changes: List[int],
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
        jobs, servers = model_dist.create()
        auction_results = {}

        for initial_cost in initial_costs:
            for price_change in price_changes:
                for server in servers:
                    server.price_change = price_change

                results = decentralised_iterative_auction(jobs, servers, time_limit, initial_cost=initial_cost)
                if results is not None:
                    auction_results['cost {}, change {}'.format(initial_cost, price_change)] = \
                        results.store(initial_cost=initial_cost, price_change=price_change)
                reset_model(jobs, servers)

        data.append(auction_results)

    # Save all of the results to a file
    filename = results_filename('iterative_round_results', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print("Successful, data saved to " + filename)
    

def basic_test(model_dist: ModelDist):
    jobs, servers = model_dist.create()
    
    job_initial = 0
    price_change = 1
    for server in servers:
        server.price_change = price_change
    results = decentralised_iterative_auction(jobs, servers, 15, initial_cost=job_initial,
                                              debug_allocation=True, debug_results=True)
    print(results.data)


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    job_initial_cost = [0, 25, 40, 60, 80]
    server_price_changes = [1, 2, 5, 10, 15]

    # round_test(loaded_model_dist, args['repeat'], job_initial_cost, server_price_changes)
    basic_test(loaded_model_dist)
