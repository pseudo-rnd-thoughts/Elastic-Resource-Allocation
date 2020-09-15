"""
Evaluating the effectiveness of the different greedy algorithms using different models, number of tasks and servers
"""

from __future__ import annotations

import json
import pprint

from auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction
from greedy.fixed_greedy import fixed_greedy_algorithm
from optimal.server_relaxed_flexible_optimal import server_relaxed_flexible_optimal
from src.core.core import reset_model, set_server_heuristics
from src.core.fixed_task import FixedTask, SumSpeedPowsFixedPolicy
from src.extra.io import parse_args, results_filename
from src.extra.model import ModelDistribution
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import policies as resource_allocation_policies
from src.greedy.server_selection_policy import policies as server_selection_policies
from src.greedy.value_density import policies as value_densities
from src.optimal.fixed_optimal import fixed_optimal
from src.optimal.flexible_optimal import flexible_optimal


# noinspection DuplicatedCode
def greedy_evaluation(model_dist: ModelDistribution, repeat_num: int, repeats: int = 50, optimal_time_limit: int = 150,
                      fixed_optimal_time_limit: int = 150, relaxed_time_limit: int = 150, with_optimal: bool = True):
    """
    Evaluation of different greedy algorithms

    :param model_dist: The model distribution
    :param repeat_num: The repeat
    :param repeats: Number of model runs
    :param optimal_time_limit: The compute time for the optimal algorithm
    :param fixed_optimal_time_limit: The compute time for the fixed optimal algorithm
    :param relaxed_time_limit: The compute time for the relaxed algorithm
    :param with_optimal: If to run the optimal algorithms
    """
    print(f'Evaluates the greedy algorithms (plus optimal, fixed and relaxed) for {model_dist.name} model with '
          f'{model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    model_results = []
    pp = pprint.PrettyPrinter()
    filename = results_filename('greedy', model_dist, repeat_num)

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        # Generate the tasks and servers
        tasks, servers = model_dist.generate()
        fixed_tasks = [FixedTask(task, SumSpeedPowsFixedPolicy()) for task in tasks]
        algorithm_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}
        pp.pprint(algorithm_results)

        if with_optimal:
            # Find the optimal solution
            optimal_result = flexible_optimal(tasks, servers, time_limit=None)
            algorithm_results[optimal_result.algorithm] = optimal_result.store()
            optimal_result.pretty_print()
            reset_model(tasks, servers)

            # Find the fixed solution
            fixed_optimal_result = fixed_optimal(fixed_tasks, servers, time_limit=None)
            algorithm_results[fixed_optimal_result.algorithm] = fixed_optimal_result.store()
            fixed_optimal_result.pretty_print()
            reset_model(fixed_tasks, servers)

            # Find the relaxed solution
            relaxed_result = server_relaxed_flexible_optimal(tasks, servers, time_limit=None)
            algorithm_results[relaxed_result.algorithm] = relaxed_result.store()
            relaxed_result.pretty_print()
            reset_model(tasks, servers)
        else:
            # Find the relaxed solution
            relaxed_result = server_relaxed_flexible_optimal(tasks, servers, relaxed_time_limit)
            algorithm_results[relaxed_result.algorithm] = relaxed_result.store()
            relaxed_result.pretty_print()
            reset_model(tasks, servers)



        # Runs the DIA as an alternative method of getting a optimal social welfare
        set_server_heuristics(servers, 3, 25)
        dia_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit=3)
        algorithm_results[dia_result.algorithm] = dia_result.store()
        dia_result.pretty_print()
        reset_model(tasks, servers)

        # Loop over all of the greedy policies permutations
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(tasks, servers, value_density, server_selection_policy,
                                                     resource_allocation_policy)
                    algorithm_results[greedy_result.algorithm] = greedy_result.store()
                    greedy_result.pretty_print()
                    reset_model(tasks, servers)

        # Loop over all of the fixed greedy policies permutations
        for value_density in value_densities:
            for server_selection_policy in server_selection_policies:
                fixed_greedy_result = fixed_greedy_algorithm(fixed_tasks, servers, value_density,
                                                             server_selection_policy)
                algorithm_results[fixed_greedy_result.algorithm] = fixed_greedy_result.store()
                fixed_greedy_result.pretty_print()
                reset_model(fixed_tasks, servers)

        # Add the results to the data
        model_results.append(algorithm_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


if __name__ == "__main__":
    args = parse_args()

    if args.extra == '' or args.extra == 'optimal':
        greedy_evaluation(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
    elif args.extra == 'time limited':
        greedy_evaluation(ModelDistribution(args.file, args.tasks, args.servers), args.repeat, with_optimal=False)
