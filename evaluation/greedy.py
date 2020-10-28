"""
Evaluating the effectiveness of the different greedy algorithms using different models, number of tasks and servers
"""

from __future__ import annotations

import json
import pprint

from src.auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction
from src.optimal.server_relaxed_flexible_optimal import server_relaxed_flexible_optimal
from src.core.core import reset_model, set_server_heuristics
from src.core.fixed_task import FixedTask, SumSpeedPowsFixedPolicy
from src.extra.io import parse_args, results_filename
from src.extra.model import ModelDistribution
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import policies as resource_allocation_policies
from src.greedy.server_selection_policy import policies as server_selection_policies
from src.greedy.task_prioritisation import policies as task_priorities, Value
from src.optimal.fixed_optimal import fixed_optimal
from src.optimal.flexible_optimal import flexible_optimal


# noinspection DuplicatedCode
def greedy_evaluation(model_dist: ModelDistribution, repeat_num: int, repeats: int = 50,
                      run_flexible: bool = True, run_fixed: bool = True):
    """
    Evaluation of different greedy algorithms

    :param model_dist: The model distribution
    :param repeat_num: The repeat
    :param repeats: Number of model runs
    :param run_flexible: If to run the optimal flexible solver
    :param run_fixed: If to run the optimal fixed solver
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
        set_server_heuristics(servers, 3, 25)
        fixed_tasks = [FixedTask(task, SumSpeedPowsFixedPolicy()) for task in tasks]
        algorithm_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}
        pp.pprint(algorithm_results)

        if run_flexible:
            # Find the optimal solution
            optimal_result = flexible_optimal(tasks, servers, time_limit=None)
            algorithm_results[optimal_result.algorithm] = optimal_result.store()
            optimal_result.pretty_print()
            reset_model(tasks, servers)

        if run_fixed:
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

        # Runs the DIA as an alternative method of getting a optimal social welfare
        dia_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit=3)
        algorithm_results[dia_result.algorithm] = dia_result.store()
        dia_result.pretty_print()
        reset_model(tasks, servers)

        # Loop over all of the greedy policies permutations
        for task_priority in task_priorities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(tasks, servers, task_priority, server_selection_policy,
                                                     resource_allocation_policy)
                    algorithm_results[greedy_result.algorithm] = greedy_result.store()
                    greedy_result.pretty_print()
                    reset_model(tasks, servers)

        # Add the results to the data
        model_results.append(algorithm_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


# noinspection DuplicatedCode
def lower_bound_testing(model_dist: ModelDistribution, repeat_num: int, repeats: int = 50):
    """
    Testing is to compare the lower bound of the greedy to the best greedy algorithm

    :param model_dist: Model distribution
    :param repeat_num: Number of repeats
    :param repeats: Repeat number
    """
    print(f'Evaluates the greedy algorithm for {model_dist.name} model with '
          f'{model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    model_results = []
    pp = pprint.PrettyPrinter()
    filename = results_filename('lower_bound', model_dist, repeat_num)

    lb_task_priorities = task_priorities + [Value()]
    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        # Generate the tasks and servers
        tasks, servers = model_dist.generate()
        algorithm_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}
        pp.pprint(algorithm_results)

        # Loop over all of the greedy policies permutations
        for task_priority in lb_task_priorities:
            for server_selection_policy in server_selection_policies:
                for resource_allocation_policy in resource_allocation_policies:
                    greedy_result = greedy_algorithm(tasks, servers, task_priority, server_selection_policy,
                                                     resource_allocation_policy)
                    algorithm_results[greedy_result.algorithm] = greedy_result.store()
                    greedy_result.pretty_print()
                    reset_model(tasks, servers)

        # Add the results to the data
        model_results.append(algorithm_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


if __name__ == "__main__":
    args = parse_args()

    if args.extra == '' or args.extra == 'full optimal':
        greedy_evaluation(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
    elif args.extra == 'fixed optimal':
        greedy_evaluation(ModelDistribution(args.file, args.tasks, args.servers), args.repeat, run_flexible=False)
    elif args.extra == 'time limited':
        greedy_evaluation(ModelDistribution(args.file, args.tasks, args.servers), args.repeat,
                          run_flexible=False, run_fixed=False)
    elif args.extra == 'lower bound':
        lower_bound_testing(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
