"""
Tests the effectiveness of the optimality time limit for the social welfare of the solution
"""

from __future__ import annotations

import json
from typing import Sequence

from branch_bound.branch_bound import branch_bound_algorithm
from branch_bound.feasibility_allocations import fixed_feasible_allocation
from core.core import reset_model
from core.fixed_task import FixedSumSpeeds, FixedTask
from core.super_server import SuperServer
from extra.io import parse_args, results_filename
from extra.model import ModelDistribution
from extra.pprint import print_model
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import SumPercentage
from greedy.server_selection_policy import SumResources
from greedy.value_density import UtilityDeadlinePerResource
from optimal.flexible_optimal import flexible_optimal_solver, flexible_optimal
from optimal.server_relaxed_flexible_optimal import server_relaxed_flexible_optimal


def test_optimal():
    model_dist = ModelDistribution('models/paper.mdl', num_tasks=20, num_servers=4)
    tasks, servers = model_dist.generate()

    greedy_result = greedy_algorithm(tasks, servers, UtilityDeadlinePerResource(), SumResources(), SumPercentage())
    print(f'\nGreedy - {greedy_result.social_welfare}')
    reset_model(tasks, servers)

    optimal_result = flexible_optimal(tasks, servers, 5)
    print(f'Optimal - {optimal_result.social_welfare}')
    reset_model(tasks, servers)

    server_relaxed_result = server_relaxed_flexible_optimal(tasks, servers, 5)
    print(f'Server relaxed - {server_relaxed_result.social_welfare}')
    reset_model(tasks, servers)


def test_optimal_deadline_factor(deadline_factors=(0, 1, 10, 50)):
    model_dist = ModelDistribution('models/paper.mdl', num_tasks=40, num_servers=8)
    for _ in range(10):
        tasks, servers = model_dist.generate()

        greedy_result = greedy_algorithm(tasks, servers, UtilityDeadlinePerResource(), SumResources(), SumPercentage())
        print(f'\nGreedy - {greedy_result.social_welfare}')
        reset_model(tasks, servers)

        for deadline_factor in deadline_factors:
            optimal_result = flexible_optimal(tasks, servers, 5, deadline_factor)
            reset_model(tasks, servers)
            server_relaxed_result = server_relaxed_flexible_optimal(tasks, servers, 5, deadline_factor)
            reset_model(tasks, servers)
            print(f'Factor: {deadline_factor} - Optimal: {optimal_result.social_welfare}, '
                  f'Relaxed: {server_relaxed_result.social_welfare}')


def test_optimal_time_limit(model_dist: ModelDistribution,
                            time_limits: Sequence[int] = (10, 30, 60, 5 * 60, 15 * 60, 60 * 60, 24 * 60 * 60)):
    """
    Tests the time limit on the social welfare

    :param model_dist: The model distribution
    :param time_limits: List of time limits to test with
    """
    tasks, servers = model_dist.generate()

    print("Models")
    print_model(tasks, servers)

    for time_limit in time_limits:
        result = flexible_optimal_solver(tasks, servers, time_limit)
        reset_model(tasks, servers)

        print(f'\tSolved completely at time limit: {time_limit}, social welfare: {result.social_welfare} '
              f'with solve time: {result.solve_time}')
        if result.data['solve status'] == 'Optimal':
            break


def optimal_testing(model_dist: ModelDistribution, repeat: int, repeats: int = 20):
    """
    Evaluates the results using the optimality

    :param model_dist: The model distribution
    :param repeat: The repeat of the testing
    :param repeats: The number of repeats
    """
    data = []
    filename = results_filename('paper', model_dist, repeat)
    for _ in range(repeats):
        tasks, servers = model_dist.generate()

        optimal_result = branch_bound_algorithm(tasks, servers)
        results = {'optimal': optimal_result.store()}
        reset_model(tasks, servers)

        relaxed_result = branch_bound_algorithm(tasks, [SuperServer(servers)])
        results['server relaxed'] = relaxed_result.store()
        reset_model(tasks, servers)

        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]
        fixed_result = branch_bound_algorithm(fixed_tasks, servers, feasibility=fixed_feasible_allocation)
        results['fixed'] = fixed_result.store()

        data.append(results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(data, file)


if __name__ == "__main__":
    args = parse_args()
    loaded_model_dist = ModelDistribution(args['model'], args['tasks'], args['servers'])

    test_optimal_time_limit(loaded_model_dist)
