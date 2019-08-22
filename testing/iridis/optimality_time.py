"""Tests the time taken for optimality"""

from __future__ import annotations

from core.model import load_dist, ModelDist, reset_model

from optimal.optimal import generate_model

from docplex.cp.model import CpoModel


def time_test(model: CpoModel, time: int):
    print("Solving for model with {} minutes".format(time//60))
    model_solution = model.solve(TimeLimit=time)
    model_solution.print_solution()
    print("\n")


if __name__ == "__main__":
    model_name, job_dist, server_dist = load_dist('models/basic.model')
    model_dist = ModelDist(model_name, job_dist, 15, server_dist, 3)

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

    time_test(model, 60 * 60)
    reset_model(jobs, servers)
