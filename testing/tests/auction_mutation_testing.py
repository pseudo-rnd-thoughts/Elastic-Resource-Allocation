"""Auction Mutation testing"""

from __future__ import annotations

import json
from random import choice
from typing import Callable

from tqdm import tqdm

from auctions.decentralised_iterative_auction import decentralised_iterative_auction

from core.core import results_filename, list_item_replacement, load_args
from core.job import Job, job_diff
from core.model import ModelDist, reset_model, load_dist


def mutated_job_test(model_dist: ModelDist, repeat: int, repeats: int = 50, price_change: int = 2,
                     time_limit: int = 15, initial_cost: Callable[[Job], int] = lambda x: 0,
                     mutate_percent: float = 0.05, mutate_repeats: int = 10):
    """
    Servers are mutated by a percent and the iterative auction run again checking the utility difference
    :param model_dist: The model
    :param repeat: The repeat number
    :param repeats: The number of repeats
    :param price_change: The default price change
    :param time_limit: The time limit on the decentralised iterative auction
    :param initial_cost: The initial cost function
    :param mutate_percent: The mutate percentage
    :param mutate_repeats: The number of mutate repeats
    """
    print("Mutate jobs and servers with iterative auctions for {} jobs and {} servers"
          .format(model_dist.num_jobs, model_dist.num_servers))
    data = []

    for _ in tqdm(range(repeats)):
        # Generate the model and set the price change to 2 as default
        jobs, servers = model_dist.create()
        for server in servers:
            server.price_change = price_change

        # Calculate the results without any mutation
        no_mutation_result = decentralised_iterative_auction(jobs, servers, time_limit, initial_cost)
        auction_results = {'no mutation': no_mutation_result.store()}

        # Save the job prices and server revenues
        job_prices = {job: job.price for job in jobs}
        allocated_jobs = {job: job.running_server is not None for job in jobs}

        # Loop each time mutating a job or server and find the auction results and compare to the unmutated result
        for _ in range(mutate_repeats):
            reset_model(jobs, servers)

            # Choice a random job and mutate it
            job: Job = choice(jobs)
            mutant_job = job.mutate(mutate_percent)

            # Replace the job with the mutant job in the job list
            list_item_replacement(jobs, job, mutant_job)

            # Find the result with the mutated job
            mutant_result = decentralised_iterative_auction(jobs, servers, time_limit, initial_cost)
            if mutant_result is not None:
                auction_results[job.name + ' job'] = \
                    mutant_result.store(difference=job_diff(job, mutant_job), mutant_value=mutant_job.price,
                                        mutated_value=job_prices[job], allocated=allocated_jobs[job])

            # Replace the mutant job with the job in the job list
            list_item_replacement(jobs, mutant_job, job)

        # Append the results to the data list
        data.append(auction_results)

    # Save all of the results to a file
    filename = results_filename('mutate_iterative_auction', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print("Successful, data saved to " + filename)


def all_job_mutations_test(model_dist: ModelDist, repeat: int, num_mutated_jobs=5, percent: float = 0.15,
                           time_limit: int = 15, initial_cost: Callable[[Job], int] = lambda x: 0):
    """
    Tests all of the mutations for an iterative auction
    :param model_dist: The model distribution
    :param repeat: The repeat number
    :param percent: The mutate percentage
    :param num_mutated_jobs: The number of mutated jobs
    :param time_limit: The time limit on the decentralised iterative auction
    :param initial_cost: The initial cost of the job
    """
    print("All mutation auction tests with {} jobs and {} servers, time limit {} sec and initial cost {} "
          .format(model_dist.num_jobs, model_dist.num_servers, time_limit, initial_cost(Job("", 0, 0, 0, 0, 0))))
    positive_percent, negative_percent = 1 + percent, 1 - percent

    # Generate the jobs and servers
    jobs, servers = model_dist.create()
    # The mutation results
    mutation_results = []

    unmutated_jobs = jobs.copy()
    # Loop, for each job then find all of the mutation of within mutate percent of the original value
    for _ in tqdm(range(num_mutated_jobs)):
        # Choice a random job
        job = choice(unmutated_jobs)
        unmutated_jobs.remove(job)

        # Loop over all of the permutations that the job requirement resources have up to the mutate percentage
        for required_storage in range(job.required_storage,
                                      int(job.required_storage * positive_percent) + 1):
            for required_computation in range(job.required_computation,
                                              int(job.required_computation * positive_percent) + 1):
                for required_results_data in range(job.required_results_data,
                                                   int(job.required_results_data * positive_percent) + 1):
                    for value in range(int(job.value * negative_percent), job.value + 1):
                        for deadline in range(int(job.deadline * negative_percent), job.deadline + 1):
                            # Create the new mutated job and create new jobs list with the mutant job replacing the job
                            mutant_job = Job('mutated ' + job.name + ' job', required_storage, required_computation,
                                             required_results_data, value, deadline)
                            list_item_replacement(jobs, job, mutant_job)

                            # Calculate the job price with the mutated job
                            result = decentralised_iterative_auction(jobs, servers, time_limit, initial_cost)
                            if result is not None:
                                mutation_results.append(result.store(difference=job_diff(mutant_job, job),
                                                                     mutant_value=mutant_job))
                                print(result.store(difference=job_diff(mutant_job, job), mutant_value=mutant_job))

                            # Remove the mutant job and read the job to the list of jobs and reset the model
                            list_item_replacement(jobs, mutant_job, job)
                            reset_model(jobs, servers)

    # Save all of the results to a file
    filename = results_filename('all_mutations_iterative_auction', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(mutation_results, file)
    print("Successful, data saved to " + filename)


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    mutated_job_test(loaded_model_dist, args['repeat'])
    # all_job_mutations_test(loaded_model_dist, args['repeat'])
