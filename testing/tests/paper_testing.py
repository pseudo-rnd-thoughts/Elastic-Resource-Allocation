"""Flexible Vs Fix job testing"""

from __future__ import annotations

import json
from typing import Dict, List

from auctions.decentralised_iterative_auction import decentralised_iterative_auction
from core.core import ImageFormat, load_args, results_filename
from core.fixed_job import FixedJob, FixedSumSpeeds
from core.job import Job
from core.model import reset_model, load_dist, ModelDist
from core.result import Result
from core.server import Server
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import SumPercentage
from greedy.server_selection_policy import SumResources
from greedy.value_density import UtilityDeadlinePerResource
from optimal.fixed_optimal import fixed_optimal_algorithm
from optimal.optimal import optimal_algorithm
from optimal.relaxed import relaxed_algorithm
from testing.analysis.greedy_analysis import plot_allocation_results


def print_results(results: Dict[str, Result]):
    """
    Print a dictionary of results
    :param results: Dictionary of results with the key as the result name
    """
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
    """
    Prints the attributes of a list of jobs in whole
    :param jobs: List of jobs
    """
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
    """
    Example flexible vs fixed test
    """
    jobs = [
        Job("Task 1",  required_storage=100, required_computation=100, required_results_data=50, deadline=10, value=100),
        Job("Task 2",  required_storage=75,  required_computation=125, required_results_data=40, deadline=10, value=90),
        Job("Task 3",  required_storage=125, required_computation=110, required_results_data=45, deadline=10, value=110),
        Job("Task 4",  required_storage=100, required_computation=75,  required_results_data=35, deadline=10, value=75),
        Job("Task 5",  required_storage=85,  required_computation=90,  required_results_data=55, deadline=10, value=125),
        Job("Task 6",  required_storage=75,  required_computation=120, required_results_data=40, deadline=10, value=100),
        Job("Task 7",  required_storage=125, required_computation=100, required_results_data=50, deadline=10, value=80),
        Job("Task 8",  required_storage=115, required_computation=75,  required_results_data=55, deadline=10, value=110),
        Job("Task 9",  required_storage=100, required_computation=110, required_results_data=60, deadline=10, value=120),
        Job("Task 10", required_storage=90,  required_computation=120, required_results_data=40, deadline=10, value=90),
        Job("Task 11", required_storage=110, required_computation=90,  required_results_data=45, deadline=10, value=100),
        Job("Task 12", required_storage=100, required_computation=80,  required_results_data=55, deadline=10, value=100)
    ]
    
    servers = [
        Server("Server 1", storage_capacity=500, computation_capacity=85, bandwidth_capacity=230),
        Server("Server 2", storage_capacity=500, computation_capacity=90, bandwidth_capacity=210),
        Server("Server 3", storage_capacity=500, computation_capacity=250, bandwidth_capacity=150)
    ]
    
    optimal_result = optimal_algorithm(jobs, servers, 20)
    print("Flexible")
    print(optimal_result.store())
    print_job_full(jobs)
    plot_allocation_results(jobs, servers, "Flexible Optimal Allocation",
                            save_formats=[ImageFormat.PNG, ImageFormat.EPS, ImageFormat.PDF], minimum_allocation=True)
    reset_model(jobs, servers)
    
    fixed_jobs = [FixedJob(job, FixedSumSpeeds(), False) for job in jobs]
    fixed_result = fixed_optimal_algorithm(fixed_jobs, servers, 20)
    print("\n\nFixed")
    print(fixed_result.store())
    print_job_full(fixed_jobs)
    plot_allocation_results(fixed_jobs, servers, "Fixed Optimal Allocation",
                            save_formats=[ImageFormat.PNG, ImageFormat.EPS, ImageFormat.PDF])

    reset_model(jobs, servers)
    
    greedy_results = greedy_algorithm(jobs, servers, UtilityDeadlinePerResource(), SumResources(), SumPercentage())
    print("\n\nGreedy")
    print(greedy_results.store())
    print_job_full(jobs)
    plot_allocation_results(jobs, servers, "Greedy Allocation",
                            save_formats=[ImageFormat.PNG, ImageFormat.EPS, ImageFormat.PDF])

    print_results({'Optimal': optimal_result, 'Fixed': fixed_result, 'Greedy': greedy_results})


def paper_testing(model_dist: ModelDist, repeat: int, repeats: int = 20):
    data = []
    for _ in range(repeats):
        jobs, servers = model_dist.create()

        results = {}
        optimal_result = optimal_algorithm(jobs, servers, 180)
        results['optimal'] = optimal_result.store()
        reset_model(jobs, servers)
        relaxed_result = relaxed_algorithm(jobs, servers, 60)
        results['relaxed'] = relaxed_result.store()
        reset_model(jobs, servers)
        fixed_jobs = [FixedJob(job, FixedSumSpeeds()) for job in jobs]
        fixed_result = fixed_optimal_algorithm(fixed_jobs, servers, 60)
        results['fixed'] = fixed_result.store()
        reset_model(jobs, servers)

        for price_change in [1, 2, 3, 5, 10]:
            dia_result = decentralised_iterative_auction(jobs, servers, 5)
            results['dia {}'.format(price_change)] = dia_result.store()

            reset_model(jobs, servers)

        data.append(results)

        # Save the results to the file
        filename = results_filename('paper', model_dist.file_name, repeat)
        with open(filename, 'w') as file:
            json.dump(data, file)


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    # example_flexible_fixed_test()
    paper_testing(loaded_model_dist, args['repeat'])
