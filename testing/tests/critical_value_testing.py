"""Critical Value testing"""

from __future__ import annotations

import json

from tqdm import tqdm

from core.core import results_filename, load_args
from core.model import ModelDist, reset_model, load_dist
from core.fixed_job import FixedJob, FixedSumSpeeds
from greedy.value_density import policies as value_densities
from greedy.server_selection_policy import policies as server_selection_policies
from greedy.resource_allocation_policy import policies as resource_allocation_policies

from auctions.decentralised_iterative_auction import decentralised_iterative_auction
from auctions.critical_value_auction import critical_value_auction
from auctions.vcg_auction import vcg_auction
from auctions.fixed_vcg_auction import fixed_vcg_auction


def critical_value_testing(model_dist: ModelDist, repeat: int, repeats: int = 50, price_change: int = 3,
                           vcg_time_limit: int = 15, fixed_vcg_time_limit: int = 15,
                           decentralised_iterative_time_limit: int = 15):
    """
    The critical value testing
    :param model_dist: The model distribution
    :param repeat: The repeat
    :param repeats: The number of repeats
    :param price_change: The price change
    :param vcg_time_limit:
    :param fixed_vcg_time_limit:
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

        # Calculate the vcg auction
        vcg_result = vcg_auction(jobs, servers, vcg_time_limit)
        auction_results['vcg'] = vcg_result.store() if vcg_result is not None else 'failure'
        reset_model(jobs, servers)

        # Calculate the fixed vcg auction
        fixed_jobs = [FixedJob(job, servers, FixedSumSpeeds()) for job in jobs]
        fixed_vcg_result = fixed_vcg_auction(fixed_jobs, servers, fixed_vcg_time_limit)
        auction_results['fixed vcg'] = fixed_vcg_result.store() if fixed_vcg_result is not None else 'failure'
        reset_model(jobs, servers)

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
    filename = results_filename('critical_values_results', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print("Successful, data saved to " + filename)


def all_policies_critical_value(model_dist: ModelDist, repeat: int, repeats: int = 50,
                                vcg_time_limit: int = 60, fixed_vcg_time_limit: int = 60):
    """
    All policies test for critical value
    :param model_dist: The model dist
    :param repeat: The repeat
    :param repeats: The number of repeats
    :param vcg_time_limit: The VCG time limit
    :param fixed_vcg_time_limit: THe Fixed VCG time limit
    """
    print("Critical value test of all policies for {} jobs and {} servers"
          .format(model_dist.num_jobs, model_dist.num_servers))
    data = []
    
    # Loop, for each run all of the algorithms
    for _ in tqdm(range(repeats)):
        # Generate the jobs and the servers
        jobs, servers = model_dist.create()
        auction_results = {}

        # Calculate the vcg auction
        vcg_result = vcg_auction(jobs, servers, vcg_time_limit)
        auction_results['vcg'] = vcg_result.store() if vcg_result is not None else 'failure'
        reset_model(jobs, servers)

        # Calculate the fixed vcg auction
        fixed_jobs = [FixedJob(job, servers, FixedSumSpeeds()) for job in jobs]
        fixed_vcg_result = fixed_vcg_auction(fixed_jobs, servers, fixed_vcg_time_limit)
        auction_results['fixed vcg'] = fixed_vcg_result.store() if fixed_vcg_result is not None else 'failure'
        reset_model(jobs, servers)
        
        # Loop over all of the greedy policies permutations
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    critical_value_result = critical_value_auction(jobs, servers, value_density,
                                                                   server_selection_policy, resource_allocation_policy)
                    auction_results[critical_value_result.algorithm_name] = critical_value_result.store()
                    reset_model(jobs, servers)
        
        # Add the results to the data
        data.append(auction_results)
    
    # Save the results to the file
    filename = results_filename('all_critical_value_test', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print("Successful, data saved to " + filename)


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    # critical_value_testing(loaded_model_dist, args['repeat'])
    all_policies_critical_value(loaded_model_dist, args['repeat'])
