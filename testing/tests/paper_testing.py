"""Flexible Vs Fix job testing"""

from __future__ import annotations

from typing import Dict, List

from auctions.critical_value_auction import critical_value_auction
from core.core import ImageFormat
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
    plot_allocation_results(jobs, servers, "Flexible Optimal Allocation", save_format=ImageFormat.PDF)
    plot_allocation_results(jobs, servers, "Flexible Optimal Allocation", save_format=ImageFormat.BOTH)
    
    fixed_jobs = [FixedJob(job, FixedSumSpeeds()) for job in jobs]
    reset_model(jobs, servers)
    fixed_result = fixed_optimal_algorithm(fixed_jobs, servers, 15)
    
    print("\n\nFixed")
    print_job_full(fixed_jobs)
    plot_allocation_results(fixed_jobs, servers, "Fixed Optimal Allocation", save_format=ImageFormat.PDF)
    plot_allocation_results(fixed_jobs, servers, "Fixed Optimal Allocation", save_format=ImageFormat.BOTH)

    reset_model(jobs, servers)

    greedy_results = greedy_algorithm(jobs, servers, UtilityDeadlinePerResource(), SumResources(), SumPercentage())

    print("\n\nGreedy")
    print_job_full(jobs)
    plot_allocation_results(jobs, servers, "Greedy Allocation", save_format=ImageFormat.PDF)
    plot_allocation_results(jobs, servers, "Greedy Allocation", save_format=ImageFormat.BOTH)

    print_results({'Optimal': optimal_result, 'Fixed': fixed_result, 'Greedy': greedy_results})


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


def debug(model_dist: ModelDist):
    jobs, servers = model_dist.create()
    critical_value_result = critical_value_auction(jobs, servers, UtilityDeadlinePerResource(),
                                                   SumResources(), SumPercentage(), debug_critical_value=True)
    print(critical_value_result.store())


if __name__ == "__main__":
    # args = load_args()

    # model_name, job_dist, server_dist = load_dist(args['model'])
    # loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    example_flexible_fixed_test()
