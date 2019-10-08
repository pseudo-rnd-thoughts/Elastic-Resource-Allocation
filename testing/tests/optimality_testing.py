"""Optimality Test"""

from __future__ import annotations

from core.core import load_args
from core.model import ModelDist, load_dist
from optimal.optimal import optimal_algorithm


def optimality_testing(model_dist: ModelDist):
    """
    Optimality testing
    :param model_dist: The model distribution
    :param repeat: The repeat
    """
    jobs, servers = model_dist.create()
    for time_limit in [10, 30, 60, 5*60, 15*60, 60*60, 24*60*60]:
        print("Time Limit: {}".format(time_limit))
        result = optimal_algorithm(jobs, servers, time_limit)
        print(result.store())
        if result.data['solve_status'] == 'Optimal':
            print("Solved completely at time limit: {}".format(time_limit))
            break


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    optimality_testing(loaded_model_dist)
