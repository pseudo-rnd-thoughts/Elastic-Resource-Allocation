"""Optimality Testing"""

from __future__ import annotations

import json
from tqdm import tqdm
import sys

from core.model import reset_model, ModelDist, load_dist

from auctions.vcg import vcg_auction
from auctions.iterative_auction import iterative_auction


def auction_price(model_dist, name, repeats=50):
    """Auction price testing"""
    epsilons = (1, 2, 3, 5, 7, 10)

    data = []

    for _ in tqdm(range(repeats)):
        jobs, servers = model_dist.create()
        results = {}

        vcg_result = vcg_auction(jobs, servers, 60)
        if vcg_result is None:
            print("VCG result fail")
            continue
        results['vcg'] = (vcg_result.total_utility, vcg_result.total_price)
        reset_model(jobs, servers)

        for epsilon in epsilons:
            iterative_result = iterative_auction(jobs, servers, 30)
            if iterative_result is None:
                print("Iterative result fail")
                continue

            iterative_prices, iterative_utilities = iterative_result
            results['iterative ' + str(epsilon)] = (iterative_utilities[-1], iterative_prices[-1])
            reset_model(jobs, servers)

        # print(results)
        data.append(results)

    with open('auction_results_{}.txt'.format(name), 'w') as outfile:
        json.dump(data, outfile)
    print("Model {} results".format(name))
    print(data)


if __name__ == "__main__":
    num_jobs = int(sys.argv[1])
    num_servers = int(sys.argv[2])
    print("Auction Test for Jobs {} Servers {} ".format(num_jobs, num_servers))
    model_name, job_dist, server_dist = load_dist('models/basic.model')
    model_dist = ModelDist(model_name, job_dist, num_jobs, server_dist, num_servers)
    auction_price(model_dist, 'j{}_s{}'.format(num_jobs, num_servers))
