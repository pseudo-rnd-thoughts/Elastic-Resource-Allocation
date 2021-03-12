"""
Tests the realistic settings
"""

import json
import pprint
from typing import List, Tuple

from src.core.core import reset_model
from src.core.fixed_task import SumSpeedPowFixedAllocationPriority, generate_fixed_tasks
from src.extra.io import parse_args, results_filename
from src.extra.model import ModelDistribution
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import policies as resource_allocation_policies
from src.greedy.server_selection_policy import policies as server_selection_policies
from src.greedy.task_prioritisation import policies as task_priorities
from src.optimal.fixed_optimal import fixed_optimal, foreknowledge_fixed_optimal
from src.optimal.flexible_optimal import flexible_optimal, server_relaxed_flexible_optimal


def model_sizing(model_dist: ModelDistribution, repeat_num: int, sizings: List[Tuple[int, int, bool, bool]],
                 repeats: int = 20):
    """
    Tests a range of possible model sizings

    :param model_dist: Model distribution
    :param repeat_num: The repeat number
    :param sizings: List of possible sizings
    :param repeats: The number of repeats
    """
    sizing_results = {}
    pp = pprint.PrettyPrinter()
    filename = results_filename('model_sizing', model_dist, repeat_num)

    for task_num, server_num, run_flexible, run_fixed in sizings:
        print(f'Sizing: ({task_num}, {server_num}), run flexible: {run_flexible}, run fixed: {run_fixed}')
        model_dist.num_tasks = task_num
        model_dist.num_servers = server_num

        repeat_results = []
        for _ in range(repeats):
            tasks, servers = model_dist.generate()
            algorithm_results = {'model': {
                'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
            }}
            pp.pprint(algorithm_results)

            if run_flexible:
                # Find the optimal solution
                optimal_result = flexible_optimal(tasks, servers, time_limit=10)
                algorithm_results[optimal_result.algorithm] = optimal_result.store()
                optimal_result.pretty_print()
                reset_model(tasks, servers)

                # Find the relaxed solution
                relaxed_result = server_relaxed_flexible_optimal(tasks, servers, time_limit=10)
                algorithm_results[relaxed_result.algorithm] = relaxed_result.store()
                relaxed_result.pretty_print()
                reset_model(tasks, servers)

            if run_fixed:
                # Find the fixed solution
                fixed_tasks = generate_fixed_tasks(tasks, SumSpeedPowFixedAllocationPriority(), False)
                fixed_optimal_result = fixed_optimal(fixed_tasks, servers, time_limit=10)
                algorithm_results[fixed_optimal_result.algorithm] = fixed_optimal_result.store()
                fixed_optimal_result.pretty_print()
                reset_model(fixed_tasks, servers)

                # Find the foreknowledge fixed solution
                foreknowledge_tasks = generate_fixed_tasks(tasks, SumSpeedPowFixedAllocationPriority(), True)
                foreknowledge_fixed_result = foreknowledge_fixed_optimal(foreknowledge_tasks, servers, time_limit=10)
                algorithm_results[foreknowledge_fixed_result.algorithm] = foreknowledge_fixed_result.store()
                foreknowledge_fixed_result.pretty_print()
                reset_model(fixed_tasks, servers)

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
        sizing_results[f'{task_num} {server_num}'] = repeat_results

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(sizing_results, file)


if __name__ == "__main__":
    args = parse_args()

    if args.extra == 'model sizing' or args.extra == '':
        model_sizing(ModelDistribution(args.file, args.tasks, args.servers), args.repeat,
                     [(10, 2, True, True), (15, 3, True, True), (20, 4, True, True), (30, 6, False, True),
                      (50, 10, False, True), (75, 15, False, False)])
