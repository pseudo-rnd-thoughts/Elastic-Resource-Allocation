"""Optimality Testing"""

from __future__ import annotations

import json
from time import time

from core.model import reset_model, ModelDist, load_dist

from auction.vcg import vcg_auction
from auction.iterative_auction import iterative_auction


def auction_price(model_dist, repeats=50):
    """Auction price testing"""
    epsilons = (1, 2, 3, 5, 7, 10)

    data = []
    vcg_time_taken = []

    for x in range(repeats):
        print("Model {}".format(x))

        jobs, servers = model_dist.create()
        results = {}

        start = time()
        vcg_result = vcg_auction(jobs, servers, 15)
        vcg_time_taken.append(time() - start)
        results['vcg'] = (vcg_result.total_utility, vcg_result.total_price)
        reset_model(jobs, servers)

        for epsilon in epsilons:
            iterative_prices, iterative_utilities = iterative_auction(jobs, servers)
            results['iterative ' + str(epsilon)] = (iterative_utilities[-1], iterative_prices[-1])
            reset_model(jobs, servers)

        data.append(results)

        print(results)

    with open('auction_results.txt', 'w') as outfile:
        json.dump(data, outfile)
    print(data)


if __name__ == "__main__":
    print("Auction Test")
    model_name, job_dist, server_dist = load_dist('models/basic.model')
    for num_jobs, num_servers in ((12, 2), (15, 3), (25, 5), (100, 20), (150, 25)):
        model_dist = ModelDist(model_name, job_dist, num_jobs, server_dist, num_servers)
        auction_price(model_dist)
