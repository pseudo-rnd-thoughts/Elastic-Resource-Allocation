"""Tests the time taken for optimality"""

from __future__ import annotations

from core.model import load_dist, ModelDist, reset_model

from optimal.optimal import generate_model

from docplex.cp.model import CpoModel


def time_test(model: CpoModel, time: int):
    """
    Time Test
    :param model: The cplex model
    :param time: The time to limit for
    """
    model_solution = model.solve(TimeLimit=time)
    print("Objective values: {}, Solve status: {}, Solve Time: {} secs"
          .format(model_solution.get_solve_status(), round(model_solution.get_solve_time(), 2),
                  model_solution.get_objective_values()))


if __name__ == "__main__":
    print("Optimality Time")
    model_name, job_dist, server_dist = load_dist('models/basic.model')
    for num_jobs, num_servers in ((12, 2), (15, 3), (25, 5), (100, 20), (150, 25)):
        model_dist = ModelDist(model_name, job_dist, num_jobs, server_dist, num_servers)
        
        for repeat in range(10):
            jobs, servers = model_dist.create()
            model, _, _, _, _ = generate_model(jobs, servers)

            time_test(model, 10)
            reset_model(jobs, servers)

            time_test(model, 60)
            reset_model(jobs, servers)

            time_test(model, 60 * 5)
            reset_model(jobs, servers)

            time_test(model, 60 * 15)
            reset_model(jobs, servers)
