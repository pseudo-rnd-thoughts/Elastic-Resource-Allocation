"""Iterative Round testing"""

from __future__ import annotations

from typing import List, Callable
import json

from tqdm import tqdm

from core.core import save_filename, load_args
from core.job import Job
from core.model import ModelDist, load_dist, reset_model
from auctions.decentralised_iterative_auction import decentralised_iterative_auction


def round_test(model_dist: ModelDist, repeat: int, initial_costs: List[Callable[[Job], int]], price_changes: List[int],
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
                reset_model(jobs, servers)
                for server in servers:
                    server.price_change = price_change

                results = decentralised_iterative_auction(jobs, servers, time_limit)
                if results is not None:
                    auction_results['cost {}, change {}'.format(initial_cost(0), price_change)] = \
                        results.store(initial_cost=initial_cost(0), price_change=price_change)
        data.append(auction_results)

    # Save all of the results to a file
    filename = save_filename('iterative_round_results', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print("Successful, data saved to " + filename)


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    def cost_lambda(c):
        """
        Create a lambda function for the cost
        :param c: The fixed cost
        :return: The lambda function
        """
        return lambda x: c
    job_initial_cost = [
        cost_lambda(cost) for cost in range(0, int(sum(dist.value_mean for dist in job_dist) / len(job_dist)), 10)
    ]
    server_price_changes = [1, 2, 5, 10, 15]

    round_test(loaded_model_dist, args['repeat'], job_initial_cost, server_price_changes)
