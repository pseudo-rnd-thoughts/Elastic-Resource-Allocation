"""
Tests the effectiveness of the optimality time limit for the social welfare of the solution
"""

from __future__ import annotations

import json
from typing import Sequence

from src.auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction
from src.core.core import reset_model, set_server_heuristics
from src.extra.io import parse_args, results_filename
from src.extra.model import ModelDistribution
from src.extra.pprint import print_model
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import SumPercentage
from src.greedy.server_selection_policy import SumResources
from src.greedy.value_density import UtilityDeadlinePerResource
from src.optimal.flexible_optimal import flexible_optimal_solver, flexible_optimal
from src.optimal.server_relaxed_flexible_optimal import server_relaxed_flexible_optimal


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
            optimal_result = flexible_optimal(tasks, servers, 5)
            reset_model(tasks, servers)
            server_relaxed_result = server_relaxed_flexible_optimal(tasks, servers, 5)
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
    filename = results_filename('testing', model_dist, repeat)
    for _ in range(repeats):
        tasks, servers = model_dist.generate()
        model_results = {}

        optimal_result = flexible_optimal(tasks, servers, 30)
        model_results[optimal_result.algorithm] = optimal_result.store()
        reset_model(tasks, servers)

        for pos in range(5):
            set_server_heuristics(servers, price_change=3, initial_price=25)
            dia_result = optimal_decentralised_iterative_auction(tasks, servers, 2)
            model_results[f'DIA {pos}'] = dia_result
            reset_model(tasks, servers)

        data.append(model_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(data, file)


if __name__ == "__main__":
    args = parse_args()
    optimal_testing(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
