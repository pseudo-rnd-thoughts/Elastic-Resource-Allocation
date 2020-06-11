"""Finds examples where in flexible job speeds are better than non flexible job speeds"""

from __future__ import annotations

from typing import List

from src.core.core import load_args
from src.core.fixed_task import FixedTask, FixedSumSpeeds
from src.core.task import Task
from src.core.model import ModelDist, load_dist, reset_model
from src.core.server import Server
from src.optimal.fixed_optimal import fixed_optimal_algorithm
from src.optimal.optimal import optimal_algorithm


def print_job_full(jobs: List[Task]):
    print("\t\tTasks")
    max_job_name_len = max(len(job.name) for job in jobs) + 1
    print("{:<{name_len}}| Value | Storage | Computation | Results | Deadline | Loading | Compute | Sending | Server"
          .format("Name", name_len=max_job_name_len))
    for job in jobs:
        # noinspection PyStringFormat
        print("{:<{name_len}}|{:^7.1f}|{:^9}|{:^13}|{:^9}|{:^10}|{:^9}|{:^9}|{:^9}|{:^10}"
              .format(job.name, job.value, job.required_storage, job.required_computation,
                      job.required_results_data, job.deadline,
                      job.loading_speed, job.compute_speed, job.sending_speed,
                      job.running_server.name if job.running_server else "None", name_len=max_job_name_len))
    print()


def print_server_full(servers: List[Server]):
    print("\t\tServers")
    max_server_name_len = max(len(server.name) for server in servers) + 1
    print("{:<{name_len}}| Storage Percent | Computation Percent | Bandwidth Percent | Tasks"
          .format("Name", name_len=max_server_name_len))
    for server in servers:
        print(f"{server.name:^{max_server_name_len}}|{(1 - server.available_storage) / server.storage_capacity:^14.3f}|"
              f"{(1 - server.available_computation) / server.computation_capacity:^14.3f}|"
              f"{(1 - server.available_bandwidth) / server.bandwidth_capacity:^14.3f}| "
              f"{','.join([job.name for job in server.allocated_jobs])}")


def fixed_comparison(model_dist: ModelDist, repeat: int, repeats: int = 1):
    for _ in range(repeats):
        jobs, servers = model_dist.create()

        print("\t\tServers")
        max_server_name_len = max(len(server.name) for server in servers) + 1
        print("{:^{name_len}}| Storage | Computation | Bandwidth".format("Name", name_len=max_server_name_len))
        for server in servers:
            print("{:<{name_len}}|{:^9}|{:^13}|{:^11}".format(server.name, server.storage_capacity,
                                                              server.computation_capacity,
                                                              server.bandwidth_capacity, name_len=max_server_name_len))

        optimal_results = optimal_algorithm(jobs, servers, 15)
        print("Optimal Solution")
        print_job_full(jobs)
        reset_model(jobs, servers)

        fixed_jobs = [FixedTask(job, servers, FixedSumSpeeds()) for job in jobs]
        print("Running fixed optimal algorithm")
        fixed_results = fixed_optimal_algorithm(fixed_jobs, servers, 15)
        print("Fixed Solution")
        print_job_full(fixed_jobs)

        print("Optimal: {}, Fixed: {}, ({}), percentage: {}"
              .format(optimal_results.data['sum value'], fixed_results.data['sum value'],
                      fixed_results.data['sum value'] / optimal_results.data['sum value'],
                      optimal_results.data['percentage jobs']))


def forced_fixed_comparison():
    jobs = [
        Task("Alice", required_storage=75, required_computation=1, required_results_data=1, deadline=1, value=1),
        Task("Bob", required_storage=100, required_computation=1, required_results_data=1, deadline=1, value=1),
        Task("Clarke", required_storage=90, required_computation=1, required_results_data=1, deadline=1, value=1),
        Task("Dug", required_storage=85, required_computation=1, required_results_data=1, deadline=1, value=1),
        Task("Eve", required_storage=1, required_computation=1, required_results_data=1, deadline=1, value=1),
        Task("Felix", required_storage=1, required_computation=1, required_results_data=1, deadline=1, value=1),
        Task("Gregory", required_storage=1, required_computation=1, required_results_data=1, deadline=1, value=1),
        Task("Hatty", required_storage=1, required_computation=1, required_results_data=1, deadline=1, value=1),
        Task("Iris", required_storage=1, required_computation=1, required_results_data=1, deadline=1, value=1),
        Task("James", required_storage=1, required_computation=1, required_results_data=1, deadline=1, value=1),
        Task("Kelly", required_storage=1, required_computation=1, required_results_data=1, deadline=1, value=1),
        Task("Liam", required_storage=1, required_computation=1, required_results_data=1, deadline=1, value=1),
    ]
    servers = [
        Server("North", storage_capacity=350, computation_capacity=1, bandwidth_capacity=1),
        Server("West", storage_capacity=400, computation_capacity=1, bandwidth_capacity=1),
        Server("South", storage_capacity=425, computation_capacity=1, bandwidth_capacity=1)
    ]

    optimal_results = optimal_algorithm(jobs, servers, 15)
    print("Optimal Solution")
    print_server_full(servers)
    reset_model(jobs, servers)

    fixed_jobs = [FixedTask(job, servers, FixedSumSpeeds()) for job in jobs]
    print("Running fixed optimal algorithm")
    fixed_results = fixed_optimal_algorithm(fixed_jobs, servers, 15)
    print("Fixed Solution")
    print_server_full(servers)

    print("Optimal: {}, Fixed: {}, percent difference: {}, job percentage: {} and {}"
          .format(optimal_results.data['sum value'], fixed_results.data['sum value'],
                  fixed_results.data['sum value'] / optimal_results.data['sum value'],
                  optimal_results.data['percentage jobs'], fixed_results.data['percentage jobs']))


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    fixed_comparison(loaded_model_dist, args['repeat'])
