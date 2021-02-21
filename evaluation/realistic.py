import json
import pprint
from typing import List, Tuple

from core.core import reset_model
from core.fixed_task import FixedTask, SumSpeedPowFixedPrioritisation
from extra.io import parse_args, results_filename
from extra.model import ModelDistribution
from greedy.greedy import greedy_algorithm
from optimal.fixed_optimal import fixed_optimal
from optimal.flexible_optimal import flexible_optimal
from optimal.server_relaxed_flexible_optimal import server_relaxed_flexible_optimal
from src.greedy.resource_allocation_policy import policies as resource_allocation_policies
from src.greedy.server_selection_policy import policies as server_selection_policies
from src.greedy.task_prioritisation import policies as task_priorities


def model_scaling(model_dist: ModelDistribution, repeat_num: int,
                  scalings: List[Tuple[int, int, int]], repeats: int = 10):
    scaling_results = {}
    pp = pprint.PrettyPrinter()
    filename = results_filename('model_scaling', model_dist, repeat_num)

    for scaling in scalings:
        print(f'Scaling: {scaling}')
        model_dist.storage_scaling = scaling[0]
        model_dist.computational_scaling = scaling[1]
        model_dist.results_data_scaling = scaling[2]

        repeat_results = []
        for _ in range(repeats):
            tasks, servers = model_dist.generate()
            fixed_tasks = [FixedTask(task, SumSpeedPowFixedPrioritisation(), resource_foreknowledge=False)
                           for task in tasks]
            foreknowledge_fixed_tasks = [FixedTask(task, SumSpeedPowFixedPrioritisation(), resource_foreknowledge=True)
                                         for task in tasks]
            algorithm_results = {'model': {
                'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
            }}
            pp.pprint(algorithm_results)

            # Find the optimal solution
            optimal_result = flexible_optimal(tasks, servers, time_limit=60 * 5)
            algorithm_results[optimal_result.algorithm] = optimal_result.store()
            optimal_result.pretty_print()
            reset_model(tasks, servers)

            # Find the fixed solution
            fixed_optimal_result = fixed_optimal(fixed_tasks, servers, time_limit=60 * 5)
            algorithm_results[fixed_optimal_result.algorithm] = fixed_optimal_result.store()
            fixed_optimal_result.pretty_print()
            reset_model(fixed_tasks, servers)

            # Find the foreknowledge fixed solution
            fixed_optimal_result = fixed_optimal(foreknowledge_fixed_tasks, servers, time_limit=60 * 5)
            algorithm_results['foreknowledge_' + fixed_optimal_result.algorithm] = fixed_optimal_result.store()
            fixed_optimal_result.pretty_print()
            reset_model(fixed_tasks, servers)

            # Find the relaxed solution
            relaxed_result = server_relaxed_flexible_optimal(tasks, servers, time_limit=60 * 5)
            algorithm_results[relaxed_result.algorithm] = relaxed_result.store()
            relaxed_result.pretty_print()
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

            repeat_results.append(algorithm_results)
        scaling_results[f'{scaling[0]} {scaling[1]} {scaling[2]}'] = repeat_results

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(scaling_results, file)


def model_sizing(model_dist: ModelDistribution, repeat_num: int, sizings: List[Tuple[int, int]],  repeats: int = 10):
    sizing_results = {}
    pp = pprint.PrettyPrinter()
    filename = results_filename('model_sizing', model_dist, repeat_num)

    for sizing in sizings:
        print(f'Sizing: {sizing}')
        model_dist.num_tasks = sizing[0]
        model_dist.num_servers = sizing[1]

        repeat_results = []
        for _ in range(repeats):
            tasks, servers = model_dist.generate()
            fixed_tasks = [FixedTask(task, SumSpeedPowFixedPrioritisation(), resource_foreknowledge=False)
                           for task in tasks]
            foreknowledge_fixed_tasks = [FixedTask(task, SumSpeedPowFixedPrioritisation(), resource_foreknowledge=True)
                                         for task in tasks]
            algorithm_results = {'model': {
                'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
            }}
            pp.pprint(algorithm_results)

            # Find the optimal solution
            optimal_result = flexible_optimal(tasks, servers, time_limit=60 * 5)
            algorithm_results[optimal_result.algorithm] = optimal_result.store()
            optimal_result.pretty_print()
            reset_model(tasks, servers)

            # Find the fixed solution
            fixed_optimal_result = fixed_optimal(fixed_tasks, servers, time_limit=60 * 5)
            algorithm_results[fixed_optimal_result.algorithm] = fixed_optimal_result.store()
            fixed_optimal_result.pretty_print()
            reset_model(fixed_tasks, servers)

            # Find the foreknowledge fixed solution
            fixed_optimal_result = fixed_optimal(foreknowledge_fixed_tasks, servers, time_limit=60 * 5)
            algorithm_results['foreknowledge_' + fixed_optimal_result.algorithm] = fixed_optimal_result.store()
            fixed_optimal_result.pretty_print()
            reset_model(fixed_tasks, servers)

            # Find the relaxed solution
            relaxed_result = server_relaxed_flexible_optimal(tasks, servers, time_limit=60 * 5)
            algorithm_results[relaxed_result.algorithm] = relaxed_result.store()
            relaxed_result.pretty_print()
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

            repeat_results.append(algorithm_results)
        sizing_results[f'{sizing[0]} {sizing[1]}'] = repeat_results

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(sizing_results, file)


if __name__ == "__main__":
    args = parse_args()

    if args.extra == '' or args.extra == 'model scaling':
        model_scaling(ModelDistribution(args.file, args.tasks, args.servers), args.repeat,
                      [(700, 1, 20), (350, 0.5, 10), (200, 0.25, 5)])
    elif args.extra == 'model sizing':
        model_sizing(ModelDistribution(args.file, args.tasks, args.servers), args.repeat,
                     [(40, 4), (60, 4), (100, 10), (100, 8)])
