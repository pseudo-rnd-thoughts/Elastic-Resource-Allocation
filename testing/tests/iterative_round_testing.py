"""Iterative Round testing"""

from __future__ import annotations

from typing import List, Callable
import json

from tqdm import tqdm

from core.core import save_filename, load_args
from core.job import Job
from core.model import ModelDist, load_dist
from auctions.decentralised_iterative_auction import decentralised_iterative_auction


def round_test(model_dist: ModelDist, repeat: int, initial_costs: List[Callable[[Job], int]], price_changes: List[int],
               repeats: int = 50, time_limit: int = 15):

    data = []

    for _ in tqdm(range(repeats)):
        jobs, servers = model_dist.create()
        auction_results = {}

        for initial_cost in initial_costs:
            for price_change in price_changes:

                for server in servers:
                    server.price_change = price_change

                results = decentralised_iterative_auction(jobs, servers, time_limit)
                auction_results['cost {}, change {}'.format(initial_cost(0), price_change)] = \
                    results.store(initial_cost=initial_cost(0), price_change=price_change)

        data.append(auction_results)

    with open(save_filename('iterative_round_results', model_dist.file_name, repeat), 'w') as file:
        json.dump(data, file)
    print("Successful")


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    job_initial_cost = [
        lambda x: cost for cost in range(0, job_dist[0].value_mean, 10)
    ]
    server_price_changes = [1, 2, 5, 10, 15]

    round_test(loaded_model_dist, args['repeat'], job_initial_cost, server_price_changes)
