"""Optimality Test"""

from __future__ import annotations

from src.core.core import load_args, print_model
from src.core.model import ModelDist, load_dist, reset_model
from src.optimal.optimal import optimal_algorithm


def optimality_testing(model_dist: ModelDist):
    """
    Optimality testing

    :param model_dist: The model distribution
    """
    tasks, servers = model_dist.create()

    print("Models")
    print_model(tasks, servers)
    for time_limit in [10, 30, 60, 5 * 60, 15 * 60, 60 * 60, 24 * 60 * 60]:
        print(f'\n\nTime Limit: {time_limit}')
        result = optimal_algorithm(tasks, servers, time_limit)
        print(result.store())
        if result.data['solve_status'] == 'Optimal':
            print(f'Solved completely at time limit: {time_limit}')
            break
        reset_model(tasks, servers)


if __name__ == "__main__":
    args = load_args()

    model_name, task_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, task_dist, args['tasks'], server_dist, args['servers'])

    optimality_testing(loaded_model_dist)
