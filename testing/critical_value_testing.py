"""Critical Value testing"""

from __future__ import annotations

import json
from typing import Callable

from tqdm import tqdm

from core.task import Task
from src.auctions.critical_value_auction import critical_value_auction
from src.auctions.decentralised_iterative_auction import decentralised_iterative_auction
from src.auctions.fixed_vcg_auction import fixed_vcg_auction
from src.auctions.vcg_auction import vcg_auction
from src.core.core import results_filename, load_args
from src.core.fixed_task import FixedTask, FixedSumSpeeds
from src.core.model import ModelDist, reset_model, load_dist
from src.greedy.resource_allocation_policy import policies as resource_allocation_policies
from src.greedy.server_selection_policy import policies as server_selection_policies
from src.greedy.value_density import policies as value_densities


def critical_value_testing(model_dist: ModelDist, repeat: int, repeats: int = 50, price_change: int = 3,
                           initial_cost: Callable[[Task], int] = lambda task: 1, vcg_time_limit: int = 15,
                           fixed_vcg_time_limit: int = 15, decentralised_iterative_time_limit: int = 15):
    """
    The critical value testing

    :param model_dist: The model distribution
    :param repeat: The repeat
    :param repeats: The number of repeats
    :param price_change: The price change
    :param initial_cost: The initial cost of the task
    :param vcg_time_limit:
    :param fixed_vcg_time_limit:
    :param decentralised_iterative_time_limit: The decentralised iterative time limit
    """
    print(f'Critical Value testing for {model_dist.num_tasks} tasks and {model_dist.num_servers} servers')

    data = []

    # Loop, for each run all of the auctions to find out the results from each type
    for _ in tqdm(range(repeats)):
        # Generate the tasks and servers
        tasks, servers = model_dist.create()
        auction_results = {}

        # Calculate the vcg auction
        vcg_result = vcg_auction(tasks, servers, vcg_time_limit)
        auction_results['vcg'] = vcg_result.store() if vcg_result is not None else 'failure'
        reset_model(tasks, servers)

        # Calculate the fixed vcg auction
        fixed_tasks = [FixedTask(task, servers, FixedSumSpeeds()) for task in tasks]
        fixed_vcg_result = fixed_vcg_auction(fixed_tasks, servers, fixed_vcg_time_limit)
        auction_results['fixed vcg'] = fixed_vcg_result.store() if fixed_vcg_result is not None else 'failure'
        reset_model(tasks, servers)

        # The decentralised iterative auction results
        for server in servers:
            server.price_change = price_change
        iterative_result = decentralised_iterative_auction(tasks, servers, decentralised_iterative_time_limit, initial_cost)
        auction_results[f'price change {price_change}'] = iterative_result.store()

        # Tests the critical value
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    reset_model(tasks, servers)
                    critical_value_result = critical_value_auction(tasks, servers, value_density,
                                                                   server_selection_policy, resource_allocation_policy)
                    auction_results[critical_value_result.algorithm_name] = critical_value_result.store()

        # Append the auction results to the data
        data.append(auction_results)

    # Save all of the results to a file
    filename = results_filename('critical_values_results', model_dist.file_name, repeat)
    with open(filename, 'w') as file:
        json.dump(data, file)
    print(f'Successful, data saved to {filename}')


def debug(model_dist: ModelDist):
    """
    Debugs the critical value testing

    :param model_dist: The model distribution
    """
    tasks, servers = model_dist.create()

    result = critical_value_auction(tasks, servers, value_densities[0], server_selection_policies[0],
                                    resource_allocation_policies[0],
                                    debug_task_value=True, debug_greedy_allocation=True, debug_critical_value=True)
    print(result.store())
    print('\t\tTask result prices')
    for task in tasks:
        print(f'Task {task.name}: {task.price}')
    """
    # Tests the critical value
    for value_density in value_densities:
        for server_selection_policy in server_selection_policies:
            for resource_allocation_policy in resource_allocation_policies:
                reset_model(tasks, servers)
                critical_value_result = critical_value_auction(tasks, servers, value_density,
                                                               server_selection_policy, resource_allocation_policy)
                print(critical_value_result.algorithm_name)
                print(critical_value_result.store())
    """


if __name__ == "__main__":
    args = load_args()

    model_name, task_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, task_dist, args['tasks'], server_dist, args['servers'])

    critical_value_testing(loaded_model_dist, args['repeat'])
