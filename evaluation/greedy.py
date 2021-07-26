"""
Evaluating the effectiveness of the different greedy algorithms using different models, number of tasks and servers
"""

from __future__ import annotations

import json
from pprint import PrettyPrinter

from src.core.core import reset_model
from src.extra.io import parse_args, results_filename
from src.extra.model import ModelDist, get_model, generate_evaluation_model
from src.greedy.greedy import greedy_algorithm, greedy_permutations
from src.greedy.resource_allocation import resource_allocation_functions, SumPowPercentage
from src.greedy.server_selection import server_selection_functions, ProductResources
from src.greedy.task_priority import task_priority_functions, ValuePriority, UtilityDeadlinePerResourcePriority, \
    ResourceSumPriority
from src.optimal.non_elastic_optimal import non_elastic_optimal
from src.optimal.elastic_optimal import elastic_optimal, server_relaxed_elastic_optimal


# noinspection DuplicatedCode
def greedy_evaluation(model_dist: ModelDist, repeat_num: int, repeats: int = 50, run_elastic_optimal: bool = True,
                      run_non_elastic_optimal: bool = True, run_server_relaxed_optimal: bool = True):
    """
    Evaluation of different greedy algorithms

    :param model_dist: The model distribution
    :param repeat_num: The repeat
    :param repeats: Number of model runs
    :param run_elastic_optimal: If to run the optimal elastic solver
    :param run_non_elastic_optimal: If to run the optimal non-elastic solver
    :param run_server_relaxed_optimal: If to run the relaxed elastic solver
    """
    print(f'Evaluates the greedy algorithms (plus elastic, non-elastic and server relaxed optimal solutions) '
          f'for {model_dist.name} model with {model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    pretty_printer, model_results = PrettyPrinter(), []
    filename = results_filename('greedy', model_dist, repeat_num)

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        tasks, servers, non_elastic_tasks, algorithm_results = generate_evaluation_model(model_dist, pretty_printer)

        if run_elastic_optimal:
            # Find the optimal solution
            elastic_optimal_result = elastic_optimal(tasks, servers, time_limit=None)
            algorithm_results[elastic_optimal_result.algorithm] = elastic_optimal_result.store()
            elastic_optimal_result.pretty_print()
            reset_model(tasks, servers)

        if run_server_relaxed_optimal:
            # Find the relaxed solution
            relaxed_result = server_relaxed_elastic_optimal(tasks, servers, time_limit=None)
            algorithm_results[relaxed_result.algorithm] = relaxed_result.store()
            relaxed_result.pretty_print()
            reset_model(tasks, servers)

        if run_non_elastic_optimal:
            # Find the non-elastic solution
            non_elastic_optimal_result = non_elastic_optimal(non_elastic_tasks, servers, time_limit=None)
            algorithm_results[non_elastic_optimal_result.algorithm] = non_elastic_optimal_result.store()
            non_elastic_optimal_result.pretty_print()
            reset_model(non_elastic_tasks, servers)

        # Loop over all of the greedy policies permutations
        greedy_permutations(tasks, servers, algorithm_results)

        # Add the results to the data
        model_results.append(algorithm_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


# noinspection DuplicatedCode
def lower_bound_testing(model_dist: ModelDist, repeat_num: int, repeats: int = 50):
    """
    Testing is to compare the lower bound of the greedy to the best greedy algorithm

    :param model_dist: Model distribution
    :param repeat_num: Number of repeats
    :param repeats: Repeat number
    """
    print(f'Evaluates the greedy algorithm for {model_dist.name} model with '
          f'{model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    pretty_printer, model_results = PrettyPrinter(), []
    filename = results_filename('lower_bound', model_dist, repeat_num)

    lb_task_functions = task_priority_functions + [ValuePriority()]
    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        tasks, servers, non_elastic_tasks, algorithm_results = generate_evaluation_model(model_dist, pretty_printer)

        # Loop over all of the greedy policies permutations
        for task_priority in lb_task_functions:
            for server_selection in server_selection_functions:
                for resource_allocation in resource_allocation_functions:
                    greedy_result = greedy_algorithm(tasks, servers, task_priority, server_selection,
                                                     resource_allocation)
                    algorithm_results[greedy_result.algorithm] = greedy_result.store()
                    greedy_result.pretty_print()
                    reset_model(tasks, servers)

        # Add the results to the data
        model_results.append(algorithm_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


def algorithm_sizes(model_dist: ModelDist, repeat_num: int, repeats: int = 30):
    """
    Runs the greedy algorithm for a range of model sizes

    :param model_dist: The model distributions
    :param repeat_num: The repeat number
    :param repeats: The number of repeats for each model size
    """
    pretty_printer, scale_results = PrettyPrinter(), {}
    filename = results_filename('greedy_model_sizes', model_dist, repeat_num)
    for num_tasks, num_servers in ((10, 2), (15, 3), (20, 4), (30, 6), (40, 8), (80, 16), (160, 32)):
        print(f'Numbers of tasks: {num_tasks}, number of servers: {num_servers}')
        model_dist.num_tasks = num_tasks
        model_dist.num_servers = num_servers

        model_results = []
        for _ in range(repeats):
            tasks, servers = model_dist.generate_oneshot()
            results = greedy_algorithm(tasks, servers,
                                       task_priority=UtilityDeadlinePerResourcePriority(ResourceSumPriority()),
                                       server_selection=ProductResources(), resource_allocation=SumPowPercentage())
            model_results.append(results.store())

        scale_results[f'{num_tasks} tasks, {num_servers} servers'] = model_results

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)


if __name__ == "__main__":
    args = parse_args()

    if args.extra == '' or args.extra == 'elastic optimal':
        greedy_evaluation(get_model(args.model, args.tasks, args.servers), args.repeat,
                          run_elastic_optimal=True, run_non_elastic_optimal=True, run_server_relaxed_optimal=True)
    elif args.extra == 'relaxed optimal':
        greedy_evaluation(get_model(args.model, args.tasks, args.servers), args.repeat,
                          run_elastic_optimal=False, run_server_relaxed_optimal=True, run_non_elastic_optimal=True)
    elif args.extra == 'non-elastic optimal':
        greedy_evaluation(get_model(args.model, args.tasks, args.servers), args.repeat,
                          run_elastic_optimal=False, run_server_relaxed_optimal=False, run_non_elastic_optimal=True)
    elif args.extra == 'greedy':
        greedy_evaluation(get_model(args.model, args.tasks, args.servers), args.repeat,
                          run_elastic_optimal=False, run_non_elastic_optimal=False, run_server_relaxed_optimal=False)
    elif args.extra == 'lower bound':
        lower_bound_testing(get_model(args.model, args.tasks, args.servers), args.repeat)
    elif args.scaling == 'model sizes':
        algorithm_sizes(get_model(args.model, args.tasks, args.servers), args.repeat)
