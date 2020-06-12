"""Flexible Vs Fix task testing"""

from __future__ import annotations

import json
from typing import Dict, List

from core.visualise import plot_allocation_results
from src.auctions.decentralised_iterative_auction import decentralised_iterative_auction
from src.core.core import ImageFormat, load_args, results_filename, reset_model
from src.core.fixed_task import FixedTask, FixedSumSpeeds
from src.core.result import Result
from src.core.server import Server
from src.core.task import Task
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import SumPercentage, SumSpeed
from src.greedy.server_selection_policy import SumResources, TaskSumResources
from src.greedy.value_density import UtilityDeadlinePerResource, UtilityPerResources, UtilityResourcePerDeadline, Value
from src.model.model_distribution import load_model_distribution, ModelDistribution
from src.optimal.fixed_optimal import fixed_optimal_algorithm
from src.optimal.optimal import optimal_algorithm
from src.optimal.relaxed import relaxed_algorithm


def print_results(results: Dict[str, Result]):
    """
    Print a dictionary of results

    :param results: Dictionary of results with the key as the result name
    """
    max_name_len = max(len(name) for name in results.keys())
    max_storage_len = max(len(f'{list(result.data["server storage usage"].values())}') for result in results.values())
    max_computation_len = max(len(f'{list(result.data["server computation usage"].values())}') for result in results.values())
    max_bandwidth_len = max(len(f'{list(result.data["server bandwidth usage"].values())}') for result in results.values())
    
    print(f"{'Name':<{max_name_len}} | Value | {'Storage':^{max_storage_len}} | {'Computation':^{max_computation_len}} | "
          f"{'Bandwidth':^{max_bandwidth_len}} | Num Tasks")
    for name, result in results.items():
        print(f"{name:<{max_name_len}} | {result.sum_value:^5} | "
              f"{'{}'.format(list(result.data['server storage usage'].values())):^{max_storage_len}} | "
              f"{'{}'.format(list(result.data['server computation usage'].values())):^{max_computation_len}} | "
              f"{'{}'.format(list(result.data['server bandwidth usage'].values())):^{max_bandwidth_len}} | "
              f"{'{}'.format(list(result.data['num tasks'].values()))}")


def print_task_full(tasks: List[Task]):
    """
    Prints the attributes of a list of tasks in whole

    :param tasks: List of tasks
    """
    print('\t\tTasks')
    max_task_name_len = max(len(task.name) for task in tasks) + 1
    print(f"{'Name':<{max_task_name_len}}| Value |{'Storage':^9}|{'Computation':^13}|{'Results':^9}|{'Deadline':^10}|"
          f"{'Loading':^9}|{'Compute':^9}|{'Sending':^9}| {'Server'}")
    for task in tasks:
        # noinspection PyStringFormat
        print(f"{task.name:<{max_task_name_len}}|{task.value:^7.1f}|{task.required_storage:^9}|"
              f"{task.required_computation:^13}|{task.required_results_data:^9}|{task.deadline:^10}|"
              f"{task.loading_speed:^9}|{task.compute_speed:^9}|{task.sending_speed:^9}|"
              f"{task.running_server.name if task.running_server else 'None':^10}")
    print()


def example_flexible_fixed_test():
    """
    Example flexible vs fixed test
    """
    tasks = [
        Task('Task 1',  required_storage=100, required_computation=100, required_results_data=50, deadline=10, value=100),
        Task('Task 2',  required_storage=75,  required_computation=125, required_results_data=40, deadline=10, value=90),
        Task('Task 3',  required_storage=125, required_computation=110, required_results_data=45, deadline=10, value=110),
        Task('Task 4',  required_storage=100, required_computation=75,  required_results_data=35, deadline=10, value=75),
        Task('Task 5',  required_storage=85,  required_computation=90,  required_results_data=55, deadline=10, value=125),
        Task('Task 6',  required_storage=75,  required_computation=120, required_results_data=40, deadline=10, value=100),
        Task('Task 7',  required_storage=125, required_computation=100, required_results_data=50, deadline=10, value=80),
        Task('Task 8',  required_storage=115, required_computation=75,  required_results_data=55, deadline=10, value=110),
        Task('Task 9',  required_storage=100, required_computation=110, required_results_data=60, deadline=10, value=120),
        Task('Task 10', required_storage=90,  required_computation=120, required_results_data=40, deadline=10, value=90),
        Task('Task 11', required_storage=110, required_computation=90,  required_results_data=45, deadline=10, value=100),
        Task('Task 12', required_storage=100, required_computation=80,  required_results_data=55, deadline=10, value=100)
    ]
    
    servers = [
        Server('Server 1', storage_capacity=500, computation_capacity=85, bandwidth_capacity=230),
        Server('Server 2', storage_capacity=500, computation_capacity=90, bandwidth_capacity=210),
        Server('Server 3', storage_capacity=500, computation_capacity=250, bandwidth_capacity=150)
    ]
    
    optimal_result = optimal_algorithm(tasks, servers, 20)
    print('Flexible')
    print(optimal_result.store())
    print_task_full(tasks)
    plot_allocation_results(tasks, servers, 'Flexible Optimal Allocation',
                            save_formats=[ImageFormat.PNG, ImageFormat.EPS, ImageFormat.PDF], minimum_allocation=True)
    reset_model(tasks, servers)
    
    fixed_tasks = [FixedTask(task, FixedSumSpeeds(), False) for task in tasks]
    fixed_result = fixed_optimal_algorithm(fixed_tasks, servers, 20)
    print('\n\nFixed')
    print(fixed_result.store())
    print_task_full(fixed_tasks)
    plot_allocation_results(fixed_tasks, servers, 'Fixed Optimal Allocation',
                            save_formats=[ImageFormat.PNG, ImageFormat.EPS, ImageFormat.PDF])

    reset_model(tasks, servers)
    
    greedy_results = greedy_algorithm(tasks, servers, UtilityDeadlinePerResource(), SumResources(), SumPercentage())
    print('\n\nGreedy')
    print(greedy_results.store())
    print_task_full(tasks)
    plot_allocation_results(tasks, servers, 'Greedy Allocation',
                            save_formats=[ImageFormat.PNG, ImageFormat.EPS, ImageFormat.PDF])

    print_results({'Optimal': optimal_result, 'Fixed': fixed_result, 'Greedy': greedy_results})


def paper_testing(model_dist: ModelDistribution, repeat: int, repeats: int = 20):
    data = []
    for _ in range(repeats):
        tasks, servers = model_dist.create()

        results = {}
        optimal_result = optimal_algorithm(tasks, servers, 180)
        results['optimal'] = optimal_result.store()
        reset_model(tasks, servers)
        relaxed_result = relaxed_algorithm(tasks, servers, 60)
        results['relaxed'] = relaxed_result.store()
        reset_model(tasks, servers)
        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]
        fixed_result = fixed_optimal_algorithm(fixed_tasks, servers, 60)
        results['fixed'] = fixed_result.store()
        reset_model(tasks, servers)

        for price_change in [1, 2, 3, 5, 10]:
            dia_result = decentralised_iterative_auction(tasks, servers, 5)
            results['dia {}'.format(price_change)] = dia_result.store()

            reset_model(tasks, servers)

        data.append(results)

        # Save the results to the file
        filename = results_filename('paper', model_dist.file_name, repeat)
        with open(filename, 'w') as file:
            json.dump(data, file)


def paper_testing_2(model_dist: ModelDistribution, repeat: int, repeats: int = 100):
    data = []
    for _ in range(repeats):
        results = {}

        tasks, servers = model_dist.create()

        greedy_policies = [
            (vd, ss, ra)
            for vd in [UtilityPerResources(), UtilityResourcePerDeadline(), UtilityDeadlinePerResource(), Value()]
            for ss in [SumResources(), SumResources(True),
                       TaskSumResources(SumPercentage()), TaskSumResources(SumPercentage(), True),
                       TaskSumResources(SumSpeed()), TaskSumResources(SumSpeed(), True)]
            for ra in [SumPercentage(), SumSpeed()]
        ]
        for (vd, ss, ra) in greedy_policies:
            try:
                greedy_result = greedy_algorithm(tasks, servers, vd, ss, ra)
                results[greedy_result.algorithm_name] = greedy_result.store()

            except Exception as e:
                print(e)

            reset_model(tasks, servers)

        data.append(results)

        # Save the results to the file
        filename = results_filename('greedy', model_dist.file_name, repeat)
        with open(filename, 'w') as file:
            json.dump(data, file)


if __name__ == "__main__":
    args = load_args()

    model_name, task_dist, server_dist = load_model_distribution(args['model'])
    loaded_model_dist = ModelDistribution(model_name, task_dist, args['tasks'], server_dist, args['servers'])

    # example_flexible_fixed_test()
    # paper_testing(loaded_model_dist, args['repeat'])
    paper_testing_2(loaded_model_dist, args['repeat'])
