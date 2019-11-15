"""Flexible Vs Fix job testing"""

from __future__ import annotations

from typing import Dict, List

from branch_bound.branch_bound import branch_bound_algorithm
from branch_bound.feasibility_allocations import fixed_feasible_allocation
from core.core import ImageFormat, load_args
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


def fog_model_testing():
    """
    FOG model testing
    """
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
    

def debug_allocation_graph():
    jobs = [
        Job("Alpha", required_storage=100, required_computation=100, required_results_data=50, deadline=10, value=100),
        Job("Beta", required_storage=75, required_computation=125, required_results_data=40, deadline=10, value=90),
        Job("Charlie", required_storage=125, required_computation=110, required_results_data=45, deadline=10, value=110),
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
        Server("X-Ray", storage_capacity=400, computation_capacity=95, bandwidth_capacity=220),
        Server("Yankee", storage_capacity=450, computation_capacity=85, bandwidth_capacity=210),
        Server("Zulu", storage_capacity=375, computation_capacity=250, bandwidth_capacity=170)
    ]
    
    greedy_results = greedy_algorithm(jobs, servers, UtilityDeadlinePerResource(), SumResources(), SumPercentage())

    print("\n\nGreedy")
    print_job_full(jobs)
    plot_allocation_results(jobs, servers, "Greedy Allocation",
                            save_formats=[ImageFormat.PNG, ImageFormat.EPS, ImageFormat.PDF])


def model_test(model_dist: ModelDist):
    for _ in range(5):
        jobs, servers = model_dist.create()
        
        optimal = optimal_algorithm(jobs, servers, 15)
        
        reset_model(jobs, servers)
        
        fixed_jobs = [FixedJob(job, FixedSumSpeeds()) for job in jobs]
        fixed = fixed_optimal_algorithm(fixed_jobs, servers, 15)
        
        reset_model(fixed_jobs, servers)
        
        greedy = greedy_algorithm(jobs, servers, UtilityDeadlinePerResource(), SumResources(), SumPercentage())
        
        print("Optimal: {}, Fixed: {}, Greedy: {}, {}".format(1, fixed.sum_value / optimal.sum_value,
                                                              greedy.sum_value / optimal.sum_value,
                                                              optimal.data['percentage jobs']))
    

if __name__ == "__main__":
    # args = load_args()

    # model_name, job_dist, server_dist = load_dist(args['model'])
    # loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    # model_test(loaded_model_dist)
    example_flexible_fixed_test()
    # debug_allocation_graph()
