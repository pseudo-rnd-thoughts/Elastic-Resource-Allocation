"""Tests the time taken for optimality"""

from __future__ import annotations

import json
import sys

from docplex.cp.model import CpoModel

from core.model import load_dist, ModelDist
from optimal.optimal import generate_model


def time_test(model: CpoModel, time: int):
    """
    Time Test
    :param model: The cplex model
    :param time: The time to limit for
    """
    model_solution = model.solve(log_output=None, RelativeOptimalityTolerance=0.025, TimeLimit=time)
    print("\tSolve time: {} secs, Solve status: {}, Objective value: {}"
          .format(round(model_solution.get_solve_time(), 2), model_solution.get_solve_status(),
                  model_solution.get_objective_values()))

    if model_solution.get_objective_values() is None:
        return None
    else:
        return model_solution.get_objective_values()[0]


if __name__ == "__main__":
    num_jobs = int(sys.argv[1])
    num_servers = int(sys.argv[2])

    print("Optimality Time for Jobs {} Servers {} ".format(num_jobs, num_servers))
    model_name, job_dist, server_dist = load_dist('models/basic.model')
    model_dist = ModelDist(model_name, job_dist, num_jobs, server_dist, num_servers)

    data = []
    for _ in range(10):
        jobs, servers = model_dist.create()
        model, _, _, _, _ = generate_model(jobs, servers)

        results = []
        for time in (10, 60, 5 * 60, 10 * 60, 30 * 60, 60 * 60):
            value = time_test(model, time)
            results.append(value)

        data.append(results)
        
    with open('optimality_results_j{}_s{}.txt'.format(num_jobs, num_servers), 'w') as outfile:
        json.dump(data, outfile)
