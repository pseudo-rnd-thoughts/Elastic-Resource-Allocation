"""
Evaluating the effect of task mutation on the results of the DIA and greedy algorithms

This is done in two parts; one investigating worsening of any task attributes and the second to investigate increasing
the value of a task for the case of military tactical networks.
"""

from __future__ import annotations

import json
import pprint
import random as rnd
from typing import TYPE_CHECKING

from src.auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction
from src.core.core import reset_model, set_server_heuristics
from src.core.task import Task
from src.extra.io import parse_args, results_filename
from src.extra.model import ModelDistribution

if TYPE_CHECKING:
    from typing import TypeVar, List

    T = TypeVar('T')


def list_item_replacement(lists: List[T], old_item: T, new_item: T):
    """
    Replace the old item in the list with the new item

    :param lists: The list
    :param old_item: The item to remove
    :param new_item: The item to append
    """
    lists.remove(old_item)
    lists.append(new_item)


def task_mutation_evaluation(model_dist: ModelDistribution, repeat_num: int, repeats: int = 25, time_limit=2,
                             price_change: int = 3, initial_price: int = 25,
                             model_mutations: int = 15, mutate_percent: float = 0.1):
    """
    Evaluates the effectiveness of a task mutations on if the mutated task is allocated and if so the difference in
        price between the mutated and normal task

    :param model_dist: Model distribution to generate tasks and servers
    :param repeat_num: The repeat number for saving the data
    :param repeats: The number of model repeats
    :param time_limit: The time limit for the decentralised iterative auction results
    :param price_change: The price change of the servers
    :param initial_price: The initial price of tasks for the servers
    :param model_mutations: The number of model mutations to attempt
    :param mutate_percent: The percentage of the model that it can be mutated by
    """
    print(f'Evaluates the possibility of tasks mutating resulting in a lower price')
    model_results = []
    pp = pprint.PrettyPrinter()
    filename = results_filename('task_mutation', model_dist, repeat_num)

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        tasks, servers = model_dist.generate()
        set_server_heuristics(servers, price_change=price_change, initial_price=initial_price)

        mutation_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}
        pp.pprint(mutation_results)

        # Calculate the results without any mutation
        no_mutation_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit=time_limit)
        no_mutation_result.pretty_print()
        mutation_results['no mutation'] = no_mutation_result.store()

        # Save the task prices and server revenues
        task_prices = {task: task.price for task in tasks}
        allocated_tasks = {task: task.running_server is not None for task in tasks}
        to_mutate_tasks = list(allocated_tasks.values())
        reset_model(tasks, servers)

        # Loop each time mutating a task or server and find the auction results and compare to the unmutated result
        for model_mutation in range(max(model_mutations, len(to_mutate_tasks))):
            # Choice a random task and mutate it
            task: Task = to_mutate_tasks.pop(rnd.randint(0, len(to_mutate_tasks) - 1))
            mutant_task = task.mutate(mutate_percent)

            # Replace the task with the mutant task in the task list
            list_item_replacement(tasks, task, mutant_task)

            # Find the result with the mutated task
            mutant_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit)
            mutation_results[f'mutation {model_mutation}'] = mutant_result.store(**{
                'task price': task_prices[task], 'task allocated': allocated_tasks[task],
                'mutant task name': task.name, 'mutant task storage': mutant_task.required_storage,
                'mutant task computation': mutant_task.required_computation,
                'mutant task results data': mutant_task.required_results_data,
                'mutant task deadline': mutant_task.deadline, 'mutant task value': mutant_task.value,
                'mutant price': mutant_task.price, 'mutant task allocated': task.running_server is not None
            })
            pp.pprint(mutation_results[f'mutation {model_mutation}'])

            # Replace the mutant task with the task in the task list
            list_item_replacement(tasks, mutant_task, task)

        # Append the results to the data list
        model_results.append(mutation_results)

        # Save all of the results to a file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


def mutation_grid_search(model_dist: ModelDistribution, repeat_num: int, percent: float = 0.15,
                         time_limit: int = 2, price_change: int = 3, initial_price: int = 15):
    """
    Attempts a grid search version of the mutation testing above where a single task is mutated in every possible way
        within a particular way to keep that the random testing is not missing anything

    :param model_dist: The model distribution to generate servers and tasks
    :param repeat_num: Program Repeat number
    :param percent: The percentage by which mutations can occur within
    :param time_limit: The time limit for the optimal decentralised iterative auction
    :param price_change: The price change of the servers
    :param initial_price: The initial price for the servers
    """
    print(f'Completes a grid search of a task known to achieve better results')
    filename = results_filename('mutation_grid_search', model_dist, repeat_num)
    positive_percent, negative_percent = 1 + percent, 1 - percent

    # Generate the tasks and servers
    tasks, servers = model_dist.generate()
    set_server_heuristics(servers, price_change=price_change, initial_price=initial_price)

    # The mutation results
    mutation_results = {'model': {
        'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
    }}

    no_mutation_dia = optimal_decentralised_iterative_auction(tasks, servers, time_limit=time_limit)
    no_mutation_dia.pretty_print()
    mutation_results['no mutation'] = no_mutation_dia.store(**{'allocated': tasks[0].running_server is not None,
                                                               'task price': tasks[0].price})
    reset_model(tasks, servers)

    task = tasks.pop()  # The original task not mutated that is randomly selected (given the tasks are already randomly generated)
    permutations = ((int(task.required_storage * positive_percent) + 1) - task.required_storage) * \
                   ((int(task.required_computation * positive_percent) + 1) - task.required_computation) * \
                   ((int(task.required_results_data * positive_percent) + 1) - task.required_results_data) * \
                   ((task.deadline + 1) - int(task.deadline * negative_percent)) * \
                   ((task.value + 1) - int(task.value * negative_percent))
    print(f'Number of permutations: {permutations}, original solve time: {no_mutation_dia.solve_time}, '
          f'estimated time: {round(permutations * no_mutation_dia.solve_time / 60, 1)} minutes')

    mutation_pos = 0
    # Loop over all of the permutations that the task requirement resources have up to the mutate percentage
    for required_storage in range(task.required_storage, int(task.required_storage * positive_percent) + 1):
        for required_computation in range(task.required_computation,
                                          int(task.required_computation * positive_percent) + 1):
            for required_results_data in range(task.required_results_data,
                                               int(task.required_results_data * positive_percent) + 1):
                for value in range(int(task.value * negative_percent), int(task.value + 1)):
                    for deadline in range(int(task.deadline * negative_percent), task.deadline + 1):
                        # Create the new mutated task and create new tasks list with the mutant task replacing the task
                        mutant_task = Task(f'mutated {task.name}', required_storage=required_storage,
                                           required_computation=required_computation,
                                           required_results_data=required_results_data, value=value, deadline=deadline)
                        tasks.append(mutant_task)

                        # Calculate the task price with the mutated task
                        mutated_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit)
                        mutated_result.pretty_print()
                        mutation_results[f'Mutation {mutation_pos}'] = mutated_result.store(**{
                            'mutated task': task.name, 'required storage': required_storage,
                            'required computation': required_computation,
                            'required results data': required_results_data, 'value': value, 'deadline': deadline,
                            'allocated': mutant_task.running_server is not None, 'task price': mutant_task.price
                        })
                        mutation_pos += 1

                        # Remove the mutant task and read the task to the list of tasks and reset the model
                        tasks.remove(mutant_task)
                        reset_model(tasks, servers)

        # Save all of the results to a file
        with open(filename, 'w') as file:
            json.dump(mutation_results, file)
    print('Finished running')


if __name__ == "__main__":
    args = parse_args()

    if args.extra == '' or args.extra == 'task mutation':
        task_mutation_evaluation(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
    elif args.extra == 'mutation grid search':
        mutation_grid_search(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
    else:
        raise Exception(f'Unknown extra argument: {args.extra}')
