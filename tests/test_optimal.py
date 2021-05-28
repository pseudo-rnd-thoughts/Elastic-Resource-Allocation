"""
Tests the effectiveness of the optimality time limit for the social welfare of the solution
"""

from __future__ import annotations

from typing import Sequence

import matplotlib.pyplot as plt

from src.core.core import reset_model
from src.core.fixed_task import generate_fixed_tasks
from src.extra.io import parse_args
from src.extra.model import ModelDist, SyntheticModelDist
from src.extra.pprint import print_model
from src.extra.visualise import minimise_resource_allocation, plot_allocation_results
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import SumPercentage
from src.greedy.server_selection_policy import SumResources
from src.greedy.task_prioritisation import UtilityDeadlinePerResource
from src.optimal.fixed_optimal import fixed_optimal
from src.optimal.flexible_optimal import flexible_optimal_solver, flexible_optimal, server_relaxed_flexible_optimal


def test_optimal_solution():
    model_dist = SyntheticModelDist(num_tasks=20, num_servers=4)
    tasks, servers = model_dist.generate_oneshot()
    fixed_tasks = generate_fixed_tasks(tasks)

    greedy_result = greedy_algorithm(tasks, servers, UtilityDeadlinePerResource(), SumResources(), SumPercentage())
    print(f'\nGreedy - {greedy_result.social_welfare}')
    reset_model(tasks, servers)

    optimal_result = flexible_optimal(tasks, servers, 5)
    print(f'Optimal - {optimal_result.social_welfare}')
    reset_model(tasks, servers)

    server_relaxed_result = server_relaxed_flexible_optimal(tasks, servers, 5)
    print(f'Server relaxed - {server_relaxed_result.social_welfare}')
    reset_model(tasks, servers)

    fixed_optimal_result = fixed_optimal(fixed_tasks, servers, 5)
    print(f'Fixed Optimal - {fixed_optimal_result.social_welfare}')
    reset_model(fixed_tasks, servers)


def test_optimal_time_limit(model_dist: ModelDist,
                            time_limits: Sequence[int] = (10, 30, 60, 5 * 60, 15 * 60, 60 * 60, 24 * 60 * 60)):
    tasks, servers = model_dist.generate_oneshot()

    print("Models")
    print_model(tasks, servers)

    for time_limit in time_limits:
        result = flexible_optimal_solver(tasks, servers, time_limit)
        reset_model(tasks, servers)

        print(f'\tSolved completely at time limit: {time_limit}, social welfare: {result.social_welfare} '
              f'with solve time: {result.solve_time}')
        if result.data['solve status'] == 'Optimal':
            break


def test_minimise_resource_allocation():
    model_dist = SyntheticModelDist(num_tasks=30, num_servers=6)
    tasks, servers = model_dist.generate_oneshot()

    flexible_optimal(tasks, servers, 5)
    plot_allocation_results(tasks, servers, "Optimal Flexible Resource Allocation", image_formats=[])
    plt.show()

    minimise_resource_allocation(tasks, servers)
    plot_allocation_results(tasks, servers, "Minimised Optimal Flexible Resource Allocation", image_formats=[])
    plt.show()


if __name__ == "__main__":
    args = parse_args()
    test_optimal_time_limit(ModelDist(args.file, args.tasks, args.servers), args.repeat)
