"""
Evaluating the effectiveness of the different auction algorithms using different models, number of tasks and servers
"""

from __future__ import annotations

import json
from pprint import PrettyPrinter

from src.auctions.critical_value_auction import critical_value_auction
from src.auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction
from src.auctions.vcg_auction import elastic_vcg_auction, non_elastic_vcg_auction
from src.core.core import reset_model
from src.extra.io import parse_args, results_filename
from src.extra.model import ModelDist, get_model, generate_evaluation_model
from src.greedy.resource_allocation import resource_allocation_functions
from src.greedy.server_selection import server_selection_functions
from src.greedy.task_priority import task_priority_functions


def auction_evaluation(model_dist: ModelDist, repeat_num: int, repeats: int = 50, dia_time_limit: int = 3,
                       run_elastic: bool = True, run_non_elastic: bool = True):
    """
    Evaluation of different auction algorithms

    :param model_dist: The model distribution
    :param repeat_num: The repeat number
    :param repeats: The number of repeats
    :param dia_time_limit: Decentralised iterative auction time limit
    :param run_elastic: If to run the elastic vcg auction
    :param run_non_elastic: If to run the non-elastic vcg auction
    """
    print(f'Evaluates the auction algorithms (cva, dia, elastic vcg, non-elastic vcg) for {model_dist.name} model with '
          f'{model_dist.num_tasks} tasks and {model_dist.num_servers} servers')
    pretty_printer, model_results = PrettyPrinter(), []
    filename = results_filename('auctions', model_dist, repeat_num)

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        tasks, servers, non_elastic_tasks, algorithm_results = generate_evaluation_model(model_dist, pretty_printer)

        if run_elastic:
            # Elastic VCG Auctions
            vcg_result = elastic_vcg_auction(tasks, servers, time_limit=None)
            algorithm_results[vcg_result.algorithm] = vcg_result.store()
            vcg_result.pretty_print()
            reset_model(tasks, servers)

        if run_non_elastic:
            # Elastic VCG auction
            vcg_result = non_elastic_vcg_auction(non_elastic_tasks, servers, time_limit=None)
            algorithm_results[vcg_result.algorithm] = vcg_result.store()
            vcg_result.pretty_print()
            reset_model(non_elastic_tasks, servers)

        # Decentralised Iterative auction
        dia_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit=dia_time_limit)
        algorithm_results[dia_result.algorithm] = dia_result.store()
        dia_result.pretty_print()
        reset_model(tasks, servers)

        # Critical Value Auction
        for task_priority in task_priority_functions:
            for server_selection_policy in server_selection_functions:
                for resource_allocation_policy in resource_allocation_functions:
                    critical_value_result = critical_value_auction(tasks, servers, task_priority,
                                                                   server_selection_policy, resource_allocation_policy)
                    algorithm_results[critical_value_result.algorithm] = critical_value_result.store()
                    critical_value_result.pretty_print()
                    reset_model(tasks, servers)

        # Add the results to the data
        model_results.append(algorithm_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


if __name__ == "__main__":
    args = parse_args()

    if args.extra == '' or args.extra == 'elastic optimal':
        auction_evaluation(get_model(args.model, args.tasks, args.servers), args.repeat,
                           run_elastic=True, run_non_elastic=True)
    elif args.extra == 'non-elastic optimal':
        auction_evaluation(get_model(args.model, args.tasks, args.servers), args.repeat,
                           run_elastic=False, run_non_elastic=True)
    elif args.extra == 'greedy':
        auction_evaluation(get_model(args.model, args.tasks, args.servers), args.repeat,
                           run_elastic=False, run_non_elastic=False)
