"""Tests to run on Southampton's Iridis 4 supercomputer"""

from tqdm import tqdm
import json
from time import time

from core.model import reset_model, ModelDist, load_dist

from optimal.optimal import optimal_algorithm

# Greedy Algorithms test
from greedy.greedy import greedy_algorithm
from greedy_matrix.matrix_greedy import matrix_greedy

from greedy.value_density import policies as value_densities
from greedy.server_selection_policy import policies as server_selection_policies
from greedy.resource_allocation_policy import policies as resource_allocation_policies
from greedy_matrix.matrix_policy import policies as matrix_policies

# Auctions test
from auction.vcg import vcg_auction
from auction.iterative_auction import iterative_auction


def greedy_test(repeats=10):
    """Greedy tests"""
    data = []
    optimal_time_taken = []
    
    model_name, job_dist, server_dist = load_dist('../models/basic.model')
    model_dist = ModelDist(model_name, job_dist, 15, server_dist, 3)
    
    for _ in tqdm(range(repeats)):
        jobs, servers = model_dist.create()
        result = {}
        
        start = time()
        optimal_result = optimal_algorithm(jobs, servers)
        optimal_time_taken.append(time() - start)
        result['Optimal'] = optimal_result.total_utility
        reset_model(jobs, servers)
        
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(jobs, servers, value_density, server_selection_policy,
                                                     resource_allocation_policy)
                    result['Greedy {} {} {}'.format(value_density.name, server_selection_policy.name,
                                                    resource_allocation_policy.name)] = greedy_result.total_utility
                    reset_model(jobs, servers)

        for policy in matrix_policies:
            greedy_matrix_result = matrix_greedy(jobs, servers, policy)
            result['Matrix ' + policy.name] = greedy_matrix_result.total_utility
            reset_model(jobs, servers)

    with open('greedy_results.txt', 'w') as outfile:
        json.dump(data, outfile)
    

def auction_price(repeats=10):
    """Auction price testing"""
    epsilons = (1, 2, 3, 5, 7, 10)
    
    data = []
    vcg_time_taken = []
    
    model_name, job_dist, server_dist = load_dist('../models/basic.model')
    model_dist = ModelDist(model_name, job_dist, 15, server_dist, 3)
    
    for _ in tqdm(range(repeats)):
        jobs, servers = model_dist.create()
        results = {}
        
        start = time()
        vcg_result = vcg_auction(jobs, servers)
        vcg_time_taken.append(time() - start)
        results['vcg'] = (vcg_result.total_utility, vcg_result.total_price)
        reset_model(jobs, servers)
        
        for epsilon in epsilons:
            iterative_prices, iterative_utilities = iterative_auction(jobs, servers)
            results['iterative ' + str(epsilon)] = (iterative_utilities[-1], iterative_prices[-1])
            reset_model(jobs, servers)
            
        data.append(results)
        
    with open('auction_results.txt', 'w') as outfile:
        json.dump(data, outfile)


if __name__ == "__main__":
    greedy_test()
    auction_price()
