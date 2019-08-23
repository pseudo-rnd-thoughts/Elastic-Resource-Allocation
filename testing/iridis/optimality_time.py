"""Tests the time taken for optimality"""

from __future__ import annotations
import sys
from tqdm import tqdm
import json

from core.model import load_dist, ModelDist, reset_model
from optimal.optimal import generate_model
from docplex.cp.model import CpoModel


def time_test(model: CpoModel, time: int):
    """
    Time Test
    :param model: The cplex model
    :param time: The time to limit for
    """
    model_solution = model.solve(log_output=None, RelativeOptimalityTolerance=0.025, TimeLimit=time)
    print("\tSolve time: {} secs, Objective value: {}, bounds: {}, gaps: {}"
          .format(round(model_solution.get_solve_time(), 2), model_solution.get_objective_values(),
                  model_solution.get_objective_bounds(), model_solution.get_objective_gaps()))
    return round(model_solution.get_solve_time(), 2), model_solution.get_objective_values()


if __name__ == "__main__":
    num_jobs = int(sys.argv[1])
    num_servers = int(sys.argv[2])
    print("Optimality Time for Jobs {} Servers {} ".format(num_jobs, num_servers))
    model_name, job_dist, server_dist = load_dist('models/basic.model')
    model_dist = ModelDist(model_name, job_dist, num_jobs, server_dist, num_servers)
    results = []
    for _ in tqdm(range(10)):
        jobs, servers = model_dist.create()
        model, _, _, _, _ = generate_model(jobs, servers)
    
        results.append(time_test(model, 10))
        reset_model(jobs, servers)
    
        results.append(time_test(model, 60))
        reset_model(jobs, servers)
    
        results.append(time_test(model, 60 * 5))
        reset_model(jobs, servers)
    
        results.append(time_test(model, 60 * 15))
        reset_model(jobs, servers)
    
        results.append(time_test(model, 60 * 60))
        reset_model(jobs, servers)
        
    with open('auction_results_j{}_s{}.txt'.format(num_jobs, num_servers), 'w') as outfile:
        json.dump(results, outfile)
