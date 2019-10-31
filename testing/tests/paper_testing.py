"""Flexible Vs Fix job testing"""

from __future__ import annotations

import json
from typing import Dict, List

from auctions.critical_value_auction import critical_value_auction
from auctions.decentralised_iterative_auction import decentralised_iterative_auction
from auctions.fixed_vcg_auction import fixed_vcg_auction
from auctions.vcg_auction import vcg_auction
from core.core import ImageFormat, results_filename, set_price_change, load_args
from core.fixed_job import FixedJob, FixedSumSpeeds
from core.job import Job
from core.model import reset_model, load_dist, ModelDist
from core.result import Result
from core.server import Server
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import SumPercentage, SumSpeed
from greedy.server_selection_policy import SumResources, Random as RandomServerSelection, JobSumResources
from greedy.value_density import UtilityPerResources, UtilityResourcePerDeadline, Random as RandomValueDensity, \
    UtilityDeadlinePerResource
from optimal.fixed_optimal import fixed_optimal_algorithm
from optimal.optimal import optimal_algorithm
from optimal.relaxed import relaxed_algorithm
from testing.analysis.greedy_analysis import plot_allocation_results


def print_results(results: Dict[str, Result]):
    max_name_len = max(len(name) for name in results.keys())
    max_storage_len = max(
        len('{}'.format(list(result.data['server storage usage'].values()))) for result in results.values())
    max_computation_len = max(
        len('{}'.format(list(result.data['server computation usage'].values()))) for result in results.values())
    max_bandwidth_len = max(
        len('{}'.format(list(result.data['server bandwidth usage'].values()))) for result in results.values())
    
    print("{:<{}} | Value | {:^{}} | {:^{}} | {:^{}} | Num Jobs"
          .format("Name", max_name_len, "Storage", max_storage_len,
                  "Computation", max_computation_len, "Bandwidth", max_bandwidth_len))
    for name, result in results.items():
        print("{:<{}} | {:^5} | {:^{}} | {:^{}} | {:^{}} | {}"
              .format(name, max_name_len, result.sum_value,
                      '{}'.format(list(result.data['server storage usage'].values())), max_storage_len,
                      '{}'.format(list(result.data['server computation usage'].values())), max_computation_len,
                      '{}'.format(list(result.data['server bandwidth usage'].values())), max_bandwidth_len,
                      '{}'.format(list(result.data['num jobs'].values()))))


def print_job_full(jobs: List[Job]):
    print("\t\tJobs")
    max_job_name_len = max(len(job.name) for job in jobs) + 1
    print("{:<{}}| Value |{:^9}|{:^13}|{:^9}|{:^10}|{:^9}|{:^9}|{:^9}| {}"
          .format("Name", max_job_name_len, "Storage", "Computation", "Results", "Deadline", "Loading", "Compute",
                  "Sending", "Server"))
    for job in jobs:
        # noinspection PyStringFormat
        print("{:<{name_len}}|{:^7.1f}|{:^9}|{:^13}|{:^9}|{:^10}|{:^9}|{:^9}|{:^9}|{:^10}"
              .format(job.name, job.value, job.required_storage, job.required_computation,
                      job.required_results_data, job.deadline,
                      job.loading_speed, job.compute_speed, job.sending_speed,
                      job.running_server.name if job.running_server else "None", name_len=max_job_name_len))
    print()


def example_flexible_fixed_test():
    jobs = [
        Job("Alpha", required_storage=100, required_computation=100, required_results_data=50, deadline=10, value=100),
        Job("Beta", required_storage=75, required_computation=125, required_results_data=40, deadline=10, value=90),
        Job("Charlie", required_storage=125, required_computation=110, required_results_data=45, deadline=10,
            value=110),
        Job("Delta", required_storage=100, required_computation=75, required_results_data=60, deadline=10, value=75),
        Job("Echo", required_storage=85, required_computation=90, required_results_data=55, deadline=10, value=125),
        Job("Foxtrot", required_storage=75, required_computation=120, required_results_data=40, deadline=10, value=100),
        Job("Golf", required_storage=125, required_computation=100, required_results_data=50, deadline=10, value=80),
        Job("Hotel", required_storage=115, required_computation=75, required_results_data=55, deadline=10, value=110),
        Job("India", required_storage=100, required_computation=110, required_results_data=60, deadline=10, value=120),
        Job("Juliet", required_storage=90, required_computation=120, required_results_data=40, deadline=10, value=90),
        Job("Kilo", required_storage=110, required_computation=90, required_results_data=45, deadline=10, value=100),
        Job("Lima", required_storage=100, required_computation=80, required_results_data=55, deadline=10, value=100)
    ]
    
    servers = [
        Server("X-Ray", storage_capacity=400, computation_capacity=100, bandwidth_capacity=220),
        Server("Yankee", storage_capacity=450, computation_capacity=100, bandwidth_capacity=210),
        Server("Zulu", storage_capacity=375, computation_capacity=90, bandwidth_capacity=250)
    ]
    
    optimal_result = optimal_algorithm(jobs, servers, 15)
    print("Flexible")
    print_job_full(jobs)
    plot_allocation_results(jobs, servers, "Flexible Optimal Allocation", save_format=ImageFormat.BOTH)
    
    fixed_jobs = [FixedJob(job, FixedSumSpeeds()) for job in jobs]
    reset_model(jobs, servers)
    fixed_result = fixed_optimal_algorithm(fixed_jobs, servers, 15)
    
    print("\n\nFixed")
    print_job_full(fixed_jobs)
    plot_allocation_results(fixed_jobs, servers, "Fixed Optimal Allocation", save_format=ImageFormat.BOTH)
    
    print_results({'Optimal': optimal_result, 'Fixed': fixed_result})


def fog_model_testing():
    model_name, job_dist, server_dist = load_dist("../../models/fog.json")
    model_dist = ModelDist(model_name, job_dist, 12, server_dist, 3)
    
    percent = []
    for _ in range(30):
        jobs, servers = model_dist.create()
        optimal_result = optimal_algorithm(jobs, servers, 15)
        
        fixed_jobs = [FixedJob(job, FixedSumSpeeds()) for job in jobs]
        reset_model(jobs, servers)
        fixed_result = fixed_optimal_algorithm(fixed_jobs, servers, 15)
        
        percent.append(round(fixed_result.sum_value / optimal_result.sum_value, 3))
        print_results({'Optimal': optimal_result, 'Fixed': fixed_result})
        print()
    
    print(sorted(percent))


def greedy_testing(model_dist: ModelDist, repeat: int, repeats: int = 100, debug_results: bool = False):
    print("Greedy testing with optimal, fixed and relaxed for {} jobs and {} servers"
          .format(model_dist.num_jobs, model_dist.num_servers))
    data = []
    for _ in range(repeats):
        jobs, servers = model_dist.create()
        results = {}

        optimal_result = optimal_algorithm(jobs, servers, 60)
        results['Optimal'] = optimal_result.store() if optimal_result else 'failure'
        if debug_results:
            print(results['Optimal'])

        reset_model(jobs, servers)

        fixed_jobs = [FixedJob(job, FixedSumSpeeds()) for job in jobs]
        fixed_result = fixed_optimal_algorithm(fixed_jobs, servers, 60)
        results['Fixed'] = fixed_result.store() if fixed_result else 'failure'
        if debug_results:
            print(results['Fixed'])

        reset_model(fixed_jobs, servers)

        relaxed_result = relaxed_algorithm(jobs, servers, 60)
        results['Relaxed'] = relaxed_result.store() if relaxed_result else 'failure'
        if debug_results:
            print(results['Relaxed'])

        reset_model(jobs, servers)

        greedy_policies = [
            (vd, ss, ra)
            for vd in [UtilityPerResources(), UtilityResourcePerDeadline(), UtilityDeadlinePerResource(),
                       RandomValueDensity()]
            for ss in [SumResources(), SumResources(True),
                       JobSumResources(SumPercentage()), JobSumResources(SumPercentage(), True),
                       JobSumResources(SumSpeed()), JobSumResources(SumSpeed(), True),
                       RandomServerSelection()]
            for ra in [SumPercentage(), SumSpeed()]
        ]
        for (vd, ss, ra) in greedy_policies:
            greedy_result = greedy_algorithm(jobs, servers, vd, ss, ra)
            results[greedy_result.algorithm_name] = greedy_result.store()
            if debug_results:
                print(results[greedy_result.algorithm_name])

            reset_model(jobs, servers)

        data.append(results)

    # Save the results to the file
    filename = results_filename('flexible_greedy', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print("Successful, data saved to " + filename)


def round_num_testing(model_dist: ModelDist, repeat: int, repeats: int = 50, debug_results: bool = False):
    print("Round Num testing for {} jobs and {} servers".format(model_dist.num_jobs, model_dist.num_servers))
    data = []
    initial_costs = [0, 20, 40, 60, 80]
    price_changes = [1, 2, 3, 5, 8]
    for _ in range(repeats):
        jobs, servers = model_dist.create()

        results = {}

        for initial_cost in initial_costs:
            for price_change in price_changes:
                set_price_change(servers, price_change)

                name = 'Initial Cost {} Price Change {}'.format(initial_cost, price_change)
                result = decentralised_iterative_auction(jobs, servers, 15, initial_cost=initial_cost)
                results[name] = result.store(initial_cost=initial_cost, price_change=price_change)

                if debug_results:
                    print(results[name])

                reset_model(jobs, servers)

        data.append(results)

    # Save the results to the file
    filename = results_filename('round_num', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print("Successful, data saved to " + filename)


def auction_testing(model_dist: ModelDist, repeat: int, repeats: int = 100, debug_results: bool = False):
    print("Auction testing with optimal, fixed and relaxed for {} jobs and {} servers"
          .format(model_dist.num_jobs, model_dist.num_servers))
    data = []
    for _ in range(repeats):
        jobs, servers = model_dist.create()
        results = {}

        vcg_result = vcg_auction(jobs, servers, 30)
        results['VCG'] = vcg_result.store() if vcg_result else 'failure'
        if debug_results:
            print(results['VCG'])

        reset_model(jobs, servers)

        fixed_jobs = [FixedJob(job, FixedSumSpeeds()) for job in jobs]
        fixed_result = fixed_vcg_auction(fixed_jobs, servers, 30)
        results['Fixed VCG'] = fixed_result.store() if fixed_result else 'failure'
        if debug_results:
            print(results['Fixed VCG'])

        reset_model(fixed_jobs, servers)

        critical_value_policies = [
            (vd, ss, ra)
            for vd in [UtilityPerResources(), UtilityResourcePerDeadline(), UtilityDeadlinePerResource()]
            for ss in [SumResources(), SumResources(True),
                       JobSumResources(SumPercentage()), JobSumResources(SumPercentage(), True),
                       JobSumResources(SumSpeed()), JobSumResources(SumSpeed(), True)]
            for ra in [SumPercentage(), SumSpeed()]
        ]
        for (vd, ss, ra) in critical_value_policies:
            critical_value_result = critical_value_auction(jobs, servers, vd, ss, ra)
            results[critical_value_result.algorithm_name] = critical_value_result.store()
            if debug_results:
                print(results[critical_value_result.algorithm_name])

            reset_model(jobs, servers)

        data.append(results)

    # Save the results to the file
    filename = results_filename('flexible_auction', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print("Successful, data saved to " + filename)


def debug(model_dist: ModelDist):
    jobs, servers = model_dist.create()
    critical_value_result = critical_value_auction(jobs, servers, UtilityDeadlinePerResource(), SumResources(), SumPercentage(), debug_critical_value=True)
    print(critical_value_result.store())


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    # greedy_testing(loaded_model_dist, args['repeat'], debug_results=True)
    # round_num_testing(loaded_model_dist, args['repeat'], debug_results=True)
    # auction_testing(loaded_model_dist, args['repeat'], debug_results=True)
