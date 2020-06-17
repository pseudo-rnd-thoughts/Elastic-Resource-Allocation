"""
Tests the effectiveness of the optimality time limit for the social welfare of the solution
"""

from __future__ import annotations

from typing import Sequence

from core.core import reset_model
from extra.io import load_args
from extra.pprint import print_model
from model.model_distribution import ModelDistribution, load_model_distribution
from optimal.optimal import optimal_algorithm


def test_optimal_time_limit(model_dist: ModelDistribution,
                            time_limits: Sequence[int] = (10, 30, 60, 5 * 60, 15 * 60, 60 * 60, 24 * 60 * 60)):
    """
    Tests the time limit on the social welfare

    :param model_dist: The model distribution
    :param time_limits: List of time limits to test with
    """
    tasks, servers = model_dist.create()

    print("Models")
    print_model(tasks, servers)

    for time_limit in time_limits:
        result = optimal_algorithm(tasks, servers, time_limit)
        reset_model(tasks, servers)

        print(f'\tSolved completely at time limit: {time_limit}, social welfare: {result.social_welfare} '
              f'with solve time: {result.solve_time}')
        if result.data['solve status'] == 'Optimal':
            break


if __name__ == "__main__":
    args = load_args()

    model_name, task_dist, server_dist = load_model_distribution(args['model'])
    loaded_model_dist = ModelDistribution(model_name, task_dist, args['tasks'], server_dist, args['servers'])

    test_optimal_time_limit(loaded_model_dist)
