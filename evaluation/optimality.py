"""Optimality Test"""

from __future__ import annotations

import json

from auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction
from branch_bound.branch_bound import branch_bound_algorithm
from branch_bound.feasibility_allocations import fixed_feasible_allocation
from core.core import reset_model
from core.fixed_task import FixedTask, FixedSumSpeeds
from extra.io import load_args
from extra.pprint import print_model
from core.super_server import SuperServer
from extra.model import ModelDistribution, results_filename
from optimal.optimal import optimal_solver


def optimality_testing(model_dist: ModelDistribution):
    """
    Optimality testing

    :param model_dist: The model distribution
    """
    tasks, servers = model_dist.generate()

    print('Models')
    print_model(tasks, servers)
    for time_limit in [10, 30, 60, 5 * 60, 15 * 60, 60 * 60, 24 * 60 * 60]:
        print(f'\n\nTime Limit: {time_limit}')
        result = optimal_solver(tasks, servers, time_limit)
        print(result.store())
        if result.data['solve_status'] == 'Optimal':
            print(f'Solved completely at time limit: {time_limit}')
            break
        reset_model(tasks, servers)


def optimal_testing(model_dist: ModelDistribution, repeat: int, repeats: int = 20):
    """
    Evaluates the results using the optimality

    :param model_dist: The model distribution
    :param repeat: The repeat of the testing
    :param repeats: The number of repeats
    """
    data = []
    for _ in range(repeats):
        tasks, servers = model_dist.generate()

        results = {}
        optimal_result = branch_bound_algorithm(tasks, servers)
        results['optimal'] = optimal_result.store()
        reset_model(tasks, servers)
        relaxed_result = branch_bound_algorithm(tasks, [SuperServer(servers)])
        results['relaxed'] = relaxed_result.store()
        reset_model(tasks, servers)
        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]
        fixed_result = branch_bound_algorithm(fixed_tasks, servers, feasibility=fixed_feasible_allocation)
        results['fixed'] = fixed_result.store()
        reset_model(tasks, servers)

        for price_change in [1, 2, 3, 5, 10]:
            dia_result = optimal_decentralised_iterative_auction(tasks, servers)
            results[f'dia {price_change}'] = dia_result.store()

            reset_model(tasks, servers)

        data.append(results)

        # Save the results to the file
        filename = results_filename('paper', model_dist, repeat)
        with open(filename, 'w') as file:
            json.dump(data, file)


if __name__ == "__main__":
    args = load_args()
    loaded_model_dist = ModelDistribution(args['model'], args['tasks'], args['servers'])

    # optimality_testing(loaded_model_dist)
    optimal_testing(loaded_model_dist, args['repeat'])
