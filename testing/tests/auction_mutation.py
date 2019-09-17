"""Auction Mutation"""

from __future__ import annotations

import json
from tqdm import tqdm
from random import choice, random

from core.core import save_filename
from core.model import ModelDist, reset_model
from core.job import Job, job_diff
from core.server import Server, server_diff

from auctions.decentralised_iterative_auction import decentralised_iterative_auction


def mutated_iterative_auction(model_dist: ModelDist, repeats: int = 50, price_change: int = 2,
                              mutate_percent: float = 0.05, mutate_repeats: int = 10, job_mutate_percent: float = 0.75):
    """Servers are mutated by a percent and the iterative auction run again checking the utility difference"""

    print("Mutate jobs and servers with iterative auctions for {} jobs and {} servers"
          .format(model_dist.num_jobs, model_dist.num_servers))

    data = []

    for _ in tqdm(range(repeats)):
        jobs, servers = model_dist.create()
        for server in servers:
            server.price_change = price_change

        results = {}

        iterative_results = decentralised_iterative_auction(jobs, servers)
        if iterative_results is None:
            print("Iterative result fail")
            continue
        iterative_prices, iterative_utilities = iterative_results
        results['no mutation'] = (iterative_utilities[-1], iterative_prices[-1], 0, 0)
        job_utilities = {job: job.utility() for job in jobs}
        server_revenue = {server: server.revenue for server in servers}
        reset_model(jobs, servers)

        for _ in range(mutate_repeats):
            if random() < job_mutate_percent:
                mutated_job: Job = choice(jobs)
                mutant_job = mutated_job.mutate(mutate_percent)

                jobs.remove(mutated_job)
                jobs.append(mutant_job)

                iterative_results = decentralised_iterative_auction(jobs, servers)
                if iterative_results is None:
                    print("Iterative result fail")
                    continue

                iterative_prices, iterative_utilities = iterative_results
                results['{} job: {}'.format(mutant_job.name, job_diff(mutated_job, mutant_job))] = \
                    (iterative_utilities[-1], iterative_prices[-1], mutant_job.utility(), job_utilities[mutated_job])

                jobs.remove(mutant_job)
                jobs.append(mutated_job)

                reset_model(jobs, servers)
            else:
                mutated_server: Server = choice(servers)
                mutant_server = mutated_server.mutate(mutate_percent)

                servers.remove(mutated_server)
                servers.append(mutant_server)

                iterative_results = decentralised_iterative_auction(jobs, servers)
                if iterative_results is None:
                    print("Iterative result fail")
                    continue

                iterative_prices, iterative_utilities = iterative_results
                results['{} server: {}'.format(mutant_server.name, server_diff(mutated_server, mutant_server))] = \
                    (iterative_utilities[-1], iterative_prices[-1],
                     mutant_server.revenue, server_revenue[mutated_server])

                servers.remove(mutant_server)
                servers.append(mutated_server)

                reset_model(jobs, servers)

        data.append(results)

    with open('mutate_iterative_auction_{}.txt'.format(model_dist.file_name), 'w') as json_file:
        json.dump(data, json_file)
    print(data)


def all_mutated_iterative_auction(model_dist, percent=0.15, num_mutated_jobs=5):
    """
    Tests all of the mutations for an iterative auction
    :param model_dist: A model distribution
    :param percent: The percent change
    :param num_mutated_jobs: The number of jobs to mutate
    """
    data = {}
    positive_percent, negative_percent = 1 + percent, 1 - percent

    jobs, servers = model_dist.create()

    result = decentralised_iterative_auction(jobs, servers)
    data['no mutate'] = result.store()

    unmutated_jobs = jobs.copy()
    for _ in range(num_mutated_jobs):
        job = choice(unmutated_jobs)
        unmutated_jobs.remove(job)
        for required_storage in range(job.required_storage,
                                      int(job.required_storage*positive_percent)+1):
            for required_computation in range(job.required_computation,
                                              int(job.required_computation*positive_percent)+1):
                for required_results_data in range(job.required_results_data,
                                                   int(job.required_results_data*positive_percent)+1):
                    for value in range(int(job.value*negative_percent), job.value+1):
                        for deadline in range(int(job.deadline*negative_percent), job.deadline+1):
                            mutated_job = Job('mutated ' + job.name, required_storage, required_computation,
                                              required_results_data, value, deadline)

                            jobs_prime = jobs.copy()
                            jobs_prime.remove(job)
                            jobs_prime.append(mutated_job)

                            result = decentralised_iterative_auction(jobs_prime, servers)
                            result_data = result.store()
                            result_data['job price'] = mutated_job.price
                            data[job_diff(job, mutated_job)] = result_data

                            reset_model(jobs, servers)

    for server in servers:
        for max_storage in range(int(server.max_storage*negative_percent), server.max_storage+1):
            for max_computation in range(int(server.max_computation*negative_percent), server.max_computation+1):
                for max_bandwidth in range(int(server.max_bandwidth*negative_percent), server.max_bandwidth+1):
                    for price_change in (1, 2, 5, 10):
                        mutated_server = Server('mutated ' + server.name, max_storage, max_computation, max_bandwidth,
                                                price_change)

                        servers_prime = servers.copy()
                        servers_prime.remove(server)
                        servers_prime.append(mutated_server)

                        result = decentralised_iterative_auction(jobs, servers_prime)
                        if result is not None:
                            result_data = result.store()
                            result_data['server revenue'] = mutated_server.revenue
                            data[server_diff(server, mutated_server)] = result_data
                        else:
                            data[server_diff(server, mutated_server)] = None

                        reset_model(jobs, servers)

    with open(save_filename('all_mutations_iterative_auction', model_dist.file_name, repeat), 'w') as json_file:
        json.dump(data, json_file)
    print(data)


if __name__ == "__main__":
    pass
