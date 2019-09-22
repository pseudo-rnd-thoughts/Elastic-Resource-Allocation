"""Optimality Testing"""

from __future__ import annotations

import json
from random import gauss

from tqdm import tqdm

from auctions.decentralised_iterative_auction import decentralised_iterative_auction
from auctions.fixed_vcg_auction import fixed_vcg_auction
from auctions.vcg_auction import vcg_auction

from core.core import load_args, save_filename
from core.model import reset_model, ModelDist, load_dist


def uniform_price_change_test(model_dist: ModelDist, repeat: int, repeats: int = 50, price_changes=(1, 2, 3, 5, 7, 10),
                              vcg_time_limit: int = 15, fixed_vcg_time_limit: int = 15,
                              decentralised_iterative_time_limit: int = 15):
    """
    Test the decentralised iterative auction where a uniform price change
    :param model_dist: The model distribution
    :param repeat: The repeat number
    :param repeats: The number of repeats
    :param price_changes: The uniform price changes
    :param vcg_time_limit: The compute time limit for vcg
    :param fixed_vcg_time_limit: The compute time limit for fixed vcg
    :param decentralised_iterative_time_limit: The compute time limit for decentralised iterative time limit
    """
    print("Single price change of {} with iterative auctions for {} jobs and {} servers"
          .format(', '.join([str(x) for x in price_changes]), model_dist.num_jobs, model_dist.num_servers))

    data = []

    # Loop, for each run all of the auctions to find out the results from each type
    for _ in tqdm(range(repeats)):
        # Generate the jobs and servers
        jobs, servers = model_dist.create()
        auction_results = {}

        # Calculate the vcg auction
        vcg_result = vcg_auction(jobs, servers, vcg_time_limit)
        auction_results['vcg'] = vcg_result.store() if vcg_result is not None else 'failure'
        reset_model(jobs, servers)

        # Calculate the fixed vcg auction
        fixed_vcg_result = fixed_vcg_auction(jobs, servers, fixed_vcg_time_limit)
        auction_results['fixed vcg'] = fixed_vcg_result.store() if vcg_result is not None else 'failure'

        # For each uniform price change, set all of the server prices to that and solve auction
        for price_change in price_changes:
            reset_model(jobs, servers)
            for server in servers:
                server.price_change = price_change

            iterative_result = decentralised_iterative_auction(jobs, servers, decentralised_iterative_time_limit)
            auction_results['price change {}'.format(price_change)] = iterative_result.store()

        # Append the auction results to the data
        data.append(auction_results)

    # Save all of the results to a file
    with open(save_filename('uniform_price_change_auction_results', model_dist.file_name, repeat), 'w') as file:
        json.dump(data, file)
    print("Successful")


def non_uniform_price_change_test(model_dist: ModelDist, repeat: int, price_changes: int = 10, repeats: int = 20,
                                  vcg_time_limit: int = 15, fixed_vcg_time_limit: int = 15,
                                  decentralised_iterative_time_limit: int = 15,
                                  price_change_mean: int = 2, price_change_std: int = 4):
    """
    Test non uniform price change servers on the decentralised iterative auction
    :param model_dist: The model distribution
    :param repeat: The repeat number
    :param price_changes: The number of price changes
    :param repeats: The number of repeats
    :param vcg_time_limit: The vcg compute time limit
    :param fixed_vcg_time_limit: The fixed vcg compute time limit
    :param decentralised_iterative_time_limit: The decentralised iterative compute time limit
    :param price_change_mean: The price change mean value
    :param price_change_std: The price change standard deviation
    """
    print("Multiple price change with iterative auctions for {} jobs and {} servers"
          .format(model_dist.num_jobs, model_dist.num_servers))
    data = []

    # Generate all of the price changes
    prices_changes = [[max(1, int(abs(gauss(price_change_mean, price_change_std))))
                       for _ in range(model_dist.num_servers)] for _ in range(price_changes)]

    # Loop, for each calculate the result for the results
    for _ in tqdm(range(repeats)):
        jobs, servers = model_dist.create()
        auction_results = {}

        # Calculate the fixed vcg auction
        vcg_result = vcg_auction(jobs, servers, vcg_time_limit)
        auction_results['vcg'] = vcg_result.store() if vcg_result is not None else 'failure'
        reset_model(jobs, servers)

        # Calculate the fixed vcg auction
        fixed_vcg_result = fixed_vcg_auction(jobs, servers, fixed_vcg_time_limit)
        auction_results['fixed vcg'] = fixed_vcg_result.store() if vcg_result is not None else 'failure'

        for price_changes in prices_changes:
            reset_model(jobs, servers)
            for server, price_change in zip(servers, price_changes):
                server.price_change = price_change

            iterative_results = decentralised_iterative_auction(jobs, servers, decentralised_iterative_time_limit)
            name = 'price change: {}'.format(', '.join([str(x) for x in price_changes]))
            auction_results[name] = iterative_results.store()

        # Append the auction results to the data
        data.append(auction_results)

    # Save the results to a file
    with open(save_filename('non_uniform_price_change_auction_results', model_dist.file_name, repeat), 'w') as file:
        json.dump(data, file)
    print("Successful")


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    uniform_price_change_test(loaded_model_dist, args['repeat'])
    # non_uniform_price_change_test(loaded_model_dist, args['repeat'])
