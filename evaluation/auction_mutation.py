"""Auction Mutation testing"""

from __future__ import annotations

import json
from random import choice
from typing import TypeVar, List

from tqdm import tqdm

from auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction
from core.core import set_price_change, reset_model
from core.task import Task, task_diff
from extra.io import load_args
from extra.model import ModelDistribution, results_filename

T = TypeVar('T')


def list_item_replacement(lists: List[T], old_item: T, new_item: T):
    """
    Replace the item in the list

    :param lists: The list
    :param old_item: The item to remove
    :param new_item: The item to append
    """

    lists.remove(old_item)
    lists.append(new_item)


def mutated_task_test(model_dist: ModelDistribution, repeats: int = 50,
                      time_limit: int = 15, price_change: int = 2, initial_cost: int = 0,
                      mutate_percent: float = 0.1, mutate_repeats: int = 10,
                      debug_results: bool = False):
    """
    Servers are mutated by a percent and the iterative auction run again checking the utility difference

    :param model_dist: The model
    :param repeats: The number of repeats
    :param price_change: The default price change
    :param time_limit: The time limit on the decentralised iterative auction
    :param initial_cost: The initial cost function
    :param mutate_percent: The mutate percentage
    :param mutate_repeats: The number of mutate repeats
    :param debug_results: If to debug the results
    """
    print(f'Mutate tasks and servers with iterative auctions for {model_dist.num_tasks} tasks and '
          f'{model_dist.num_servers} servers')
    data = []

    for _ in tqdm(range(repeats)):
        # Generate the model and set the price change to 2 as default
        tasks, servers = model_dist.generate()
        set_price_change(servers, price_change)

        # Calculate the results without any mutation
        no_mutation_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit)
        auction_results = {'no mutation': no_mutation_result.store()}

        # Save the task prices and server revenues
        task_prices = {task: task.price for task in tasks}
        allocated_tasks = {task: task.running_server is not None for task in tasks}

        # Loop each time mutating a task or server and find the auction results and compare to the unmutated result
        for _ in range(mutate_repeats):
            reset_model(tasks, servers)

            # Choice a random task and mutate it
            task: Task = choice(tasks)
            mutant_task = task.mutate(mutate_percent)

            # Replace the task with the mutant task in the task list
            list_item_replacement(tasks, task, mutant_task)

            # Find the result with the mutated task
            mutant_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit)
            if mutant_result is not None:
                auction_results[f'{task.name} task'] = \
                    mutant_result.store(difference=task_diff(task, mutant_task), mutant_value=mutant_task.price,
                                        mutated_value=task_prices[task], allocated=allocated_tasks[task])
                if debug_results:
                    print(auction_results[f'{task.name} task'])

            # Replace the mutant task with the task in the task list
            list_item_replacement(tasks, mutant_task, task)

        # Append the results to the data list
        data.append(auction_results)
        print(auction_results)

        # Save all of the results to a file
        filename = results_filename('mutate_iterative_auction', model_dist, 1)
        with open(filename, 'w') as file:
            json.dump(data, file)


def all_task_mutations_test(model_dist: ModelDistribution, repeat: int, num_mutated_tasks=5, percent: float = 0.15,
                            time_limit: int = 15, initial_cost: int = 0, debug_results: bool = False):
    """
    Tests all of the mutations for an iterative auction

    :param model_dist: The model distribution
    :param repeat: The repeat number
    :param percent: The mutate percentage
    :param num_mutated_tasks: The number of mutated tasks
    :param time_limit: The time limit on the decentralised iterative auction
    :param initial_cost: The initial cost of the task
    :param debug_results: If to debug the results
    """
    print(f'All mutation auction tests with {model_dist.num_tasks} tasks and {model_dist.num_servers} servers, '
          f'time limit {time_limit} sec and initial cost {initial_cost} ')
    positive_percent, negative_percent = 1 + percent, 1 - percent

    # Generate the tasks and servers
    tasks, servers = model_dist.generate()
    # The mutation results
    mutation_results = []

    task = tasks[0]
    permutations = ((int(task.required_storage * positive_percent) + 1) - task.required_storage) * \
                   ((int(task.required_computation * positive_percent) + 1) - task.required_computation) * \
                   ((int(task.required_results_data * positive_percent) + 1) - task.required_results_data) * \
                   ((task.deadline + 1) - int(task.deadline * negative_percent)) * \
                   ((task.value + 1) - int(task.value * negative_percent))
    print(f'Number of permutations: {permutations}')

    unmutated_tasks = tasks.copy()
    # Loop, for each task then find all of the mutation of within mutate percent of the original value
    for _ in tqdm(range(num_mutated_tasks)):
        # Choice a random task
        task = choice(unmutated_tasks)
        unmutated_tasks.remove(task)

        # Loop over all of the permutations that the task requirement resources have up to the mutate percentage
        for required_storage in range(task.required_storage,
                                      int(task.required_storage * positive_percent) + 1):
            for required_computation in range(task.required_computation,
                                              int(task.required_computation * positive_percent) + 1):
                for required_results_data in range(task.required_results_data,
                                                   int(task.required_results_data * positive_percent) + 1):
                    for value in range(int(task.value * negative_percent), task.value + 1):
                        for deadline in range(int(task.deadline * negative_percent), task.deadline + 1):
                            # Create the new mutated task and create new tasks list with the mutant task replacing the task
                            mutant_task = Task(f'mutated {task.name} task', required_storage, required_computation,
                                               required_results_data, value, deadline)
                            list_item_replacement(tasks, task, mutant_task)

                            # Calculate the task price with the mutated task
                            result = optimal_decentralised_iterative_auction(tasks, servers, time_limit)
                            if result is not None:
                                mutation_results.append(result.store(difference=task_diff(mutant_task, task),
                                                                     mutant_value=mutant_task))
                                if debug_results:
                                    print(
                                        result.store(difference=task_diff(mutant_task, task), mutant_value=mutant_task))

                            # Remove the mutant task and read the task to the list of tasks and reset the model
                            list_item_replacement(tasks, mutant_task, task)
                            reset_model(tasks, servers)

        # Save all of the results to a file
        filename = results_filename('all_mutations_iterative_auction', model_dist, repeat)
        with open(filename, 'w') as file:
            json.dump(mutation_results, file)


if __name__ == "__main__":
    args = load_args()
    loaded_model_dist = ModelDistribution(args['model'], args['tasks'], args['servers'])

    mutated_task_test(loaded_model_dist, time_limit=5)
    # all_task_mutations_test(loaded_model_dist, args['repeat'])
