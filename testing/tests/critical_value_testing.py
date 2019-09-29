"""Critical Value testing"""

from __future__ import annotations

import json

from tqdm import tqdm

from core.core import save_filename, load_args
from core.model import ModelDist, reset_model, load_dist

from greedy.value_density import policies as value_densities
from greedy.server_selection_policy import policies as server_selection_policies
from greedy.resource_allocation_policy import policies as resource_allocation_policies

from auctions.decentralised_iterative_auction import decentralised_iterative_auction
from auctions.critical_value_auction import critical_value_auction


def critical_value_testing(model_dist: ModelDist, repeat: int, repeats: int = 50, price_change: int = 3,
                           decentralised_iterative_time_limit: int = 15):
    """
    The critical value testing
    :param model_dist: The model distribution
    :param repeat: The repeat
    :param repeats: The number of repeats
    :param price_change: The price change
    :param decentralised_iterative_time_limit: The decentralised iterative time limit
    """
    print("Critical Value testing for {} jobs and {} servers"
          .format(model_dist.num_jobs, model_dist.num_servers))

    data = []

    # Loop, for each run all of the auctions to find out the results from each type
    for _ in tqdm(range(repeats)):
        # Generate the jobs and servers
        jobs, servers = model_dist.create()
        auction_results = {}

        # The decentralised iterative auction results
        for server in servers:
            server.price_change = price_change
        iterative_result = decentralised_iterative_auction(jobs, servers, decentralised_iterative_time_limit)
        auction_results['price change {}'.format(price_change)] = iterative_result.store()

        # Tests the critical value
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    reset_model(jobs, servers)
                    critical_value_result = critical_value_auction(jobs, servers, value_density,
                                                                   server_selection_policy, resource_allocation_policy)
                    auction_results[critical_value_result.algorithm_name] = critical_value_result.store()

        # Append the auction results to the data
        data.append(auction_results)

    # Save all of the results to a file
    filename = save_filename('critical_values_results', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print("Successful, data saved to " + filename)


def debug(model_dist: ModelDist):
    """
    Debugs the critical value testing
    :param model_dist: The model distribution
    """
    jobs, servers = model_dist.create()

    result = critical_value_auction(jobs, servers, value_densities[0], server_selection_policies[0],
                                    resource_allocation_policies[0],
                                    debug_job_value=True, debug_greedy_allocation=True, debug_critical_value=True)
    print(result.store())
    print("\t\tJob result prices")
    for job in jobs:
        print("Job {}: {}".format(job.name, job.price))
    """
    # Tests the critical value
    for value_density in value_densities:
        for server_selection_policy in server_selection_policies:
            for resource_allocation_policy in resource_allocation_policies:
                reset_model(jobs, servers)
                critical_value_result = critical_value_auction(jobs, servers, value_density,
                                                               server_selection_policy, resource_allocation_policy)
                print(critical_value_result.algorithm_name)
                print(critical_value_result.store())
    """


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    critical_value_testing(loaded_model_dist, args['repeat'])
