"""Optimality Test"""

from __future__ import annotations

import json

from auctions import decentralised_iterative_auction
from branch_bound import branch_bound_algorithm
from branch_bound import fixed_feasible_allocation
from core import load_args, print_model, results_filename
from core import FixedJob, FixedSumSpeeds
from core import ModelDist, load_dist, reset_model
from core import SuperServer
from optimal import optimal_algorithm


def optimality_testing(model_dist: ModelDist):
    """
    Optimality testing
    :param model_dist: The model distribution
    """
    jobs, servers = model_dist.create()

    print("Models")
    print_model(jobs, servers)
    for time_limit in [10, 30, 60, 5*60, 15*60, 60*60, 24*60*60]:
        print("\n\nTime Limit: {}".format(time_limit))
        result = optimal_algorithm(jobs, servers, time_limit)
        print(result.store())
        if result.data['solve_status'] == 'Optimal':
            print("Solved completely at time limit: {}".format(time_limit))
            break
        reset_model(jobs, servers)


def optimal_testing(model_dist: ModelDist, repeat: int, repeats: int = 20):
    data = []
    for _ in range(repeats):
        jobs, servers = model_dist.create()

        results = {}
        optimal_result = branch_bound_algorithm(jobs, servers)
        results['optimal'] = optimal_result.store()
        reset_model(jobs, servers)
        relaxed_result = branch_bound_algorithm(jobs, [SuperServer(servers)])
        results['relaxed'] = relaxed_result.store()
        reset_model(jobs, servers)
        fixed_jobs = [FixedJob(job, FixedSumSpeeds()) for job in jobs]
        fixed_result = branch_bound_algorithm(fixed_jobs, servers, feasibility=fixed_feasible_allocation)
        results['fixed'] = fixed_result.store()
        reset_model(jobs, servers)

        for price_change in [1, 2, 3, 5, 10]:
            dia_result = decentralised_iterative_auction(jobs, servers, 5)
            results['dia {}'.format(price_change)] = dia_result.store()

            reset_model(jobs, servers)

        data.append(results)

        # Save the results to the file
        filename = results_filename('paper', model_dist.file_name, repeat)
        with open(filename, 'w') as file:
            json.dump(data, file)


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    # optimality_testing(loaded_model_dist)
    optimal_testing(loaded_model_dist, args['repeat'])
