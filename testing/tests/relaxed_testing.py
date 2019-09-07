"""Relaxed optimality testing"""

import sys
import json

from core.server import Server
from core.model import load_dist, ModelDist
from optimal.relaxed import generate_model as relaxed_generate_model
from optimal.optimal import generate_model as optimal_generate_model

from docplex.cp.model import CpoModel


def time_test(model: CpoModel, time_limit: int, name: str):
    """
    Time Test
    :param name:
    :param model: The cplex model
    :param time_limit: The time to limit for
    """
    model_solution = model.solve(log_output=None, RelativeOptimalityTolerance=0.025, TimeLimit=time_limit)
    print("\t{} - Solve time: {} secs, Solve status: {}, Objective value: {}"
          .format(name, round(model_solution.get_solve_time(), 2), model_solution.get_solve_status(),
                  model_solution.get_objective_values()))

    if model_solution.get_objective_values() is None:
        return None, "{} secs".format(round(model_solution.get_solve_time(), 2))
    else:
        return model_solution.get_objective_values()[0], "{} secs".format(round(model_solution.get_solve_time(), 2))


if __name__ == "__main__":
    num_jobs = int(sys.argv[1])
    num_servers = int(sys.argv[2])

    print("Optimality Time for Jobs {} Servers {} ".format(num_jobs, num_servers))
    model_name, job_dist, server_dist = load_dist('models/basic.model')
    model_dist = ModelDist(model_name, job_dist, num_jobs, server_dist, num_servers)

    data = []
    for _ in range(20):
        jobs, servers = model_dist.create()

        relaxed_model, _, _, _, _, _ = relaxed_generate_model(jobs, servers)
        optimal_model, _, _, _, _ = optimal_generate_model(jobs, servers)

        time_data = {}
        for time in (10, 60, 5 * 60, 10 * 60):
            relaxed_value = time_test(relaxed_model, time, 'Relax')
            optimal_value = time_test(optimal_model, time, 'Optimal')

            time_data["{} sec".format(time)] = {'relaxed': relaxed_value, 'optimal': optimal_value}

        data.append(time_data)

    with open('relaxed_results_j{}_s{}.txt'.format(num_jobs, num_servers), 'w') as outfile:
        json.dump(data, outfile)
