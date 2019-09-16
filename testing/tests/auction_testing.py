"""Optimality Testing"""

from __future__ import annotations

import json
from random import gauss

from tqdm import tqdm

from auctions.decentralised_iterative_auction import decentralised_iterative_auction
from auctions.fixed_vcg_auction import fixed_vcg_auction
from auctions.vcg_auction import vcg_auction
from core.func import load_args
from core.model import reset_model, ModelDist, load_dist


def single_price_iterative_auction(model_dist: ModelDist, repeats: int = 50):
    """Price change iterative auction testing"""
    price_changes = (1, 2, 3, 5, 7, 10)
    data = []

    print("Single price change of {} with iterative auctions for {} jobs and {} servers"
          .format(', '.join([str(x) for x in price_changes]), model_dist.num_jobs, model_dist.num_servers))

    for _ in tqdm(range(repeats)):
        jobs, servers = model_dist.create()
        results = {}

        vcg_result = vcg_auction(jobs, servers)
        if vcg_result is None:
            print("VCG result fail")
            continue
        results['vcg'] = vcg_result.sum_value
        reset_model(jobs, servers)

        cda_result = fixed_vcg_auction(jobs, servers)
        if cda_result is None:
            print("CDA result fail")
            continue
        results['cda'] = cda_result.sum_value
        reset_model(jobs, servers)

        for price_change in price_changes:
            for server in servers:
                server.price_change = price_change

            iterative_result = decentralised_iterative_auction(jobs, servers)
            if iterative_result is None:
                print("Iterative result fail")
                continue

            iterative_prices, iterative_utilities = iterative_result
            results['price change {}'.format(price_change)] = iterative_utilities[-1]
            reset_model(jobs, servers)

        # print(results)
        data.append(results)

    with open('single_price_iterative_auction_results_{}.txt'.format(model_dist.file_name), 'w') as outfile:
        json.dump(data, outfile)
    print(data)


def multi_price_change_iterative_auction(model_dist: ModelDist, changes: int = 10, repeats: int = 20):
    """Multi price change iterative auction testing"""
    print("Multiple price change with iterative auctions for {} jobs and {} servers"
          .format(model_dist.num_jobs, model_dist.num_servers))

    prices_changes = [[max(1, int(abs(gauss(0, 5)))) for _ in range(model_dist.num_servers)] for _ in range(changes)]
    data = []

    for _ in tqdm(range(repeats)):
        jobs, servers = model_dist.create()
        results = {}

        for price_changes in prices_changes:
            for server, price_change in zip(servers, price_changes):
                server.price_change = price_change

            iterative_results = decentralised_iterative_auction(jobs, servers)
            if iterative_results is None:
                print("Iterative result fail")
                continue

            # TODO add results
            reset_model(jobs, servers)

        data.append(results)

    with open('multi_price_iterative_auction_results_{}.txt'.format(model_dist.file_name), 'w') as outfile:
        json.dump(data, outfile)
    print(data)


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist('models/basic.model')
    basic_model_dist = ModelDist(model_name, job_dist, num_jobs, server_dist, num_servers)

    # single_price_iterative_auction(basic_model_dist)
    # multi_price_change_iterative_auction(basic_model_dist)
