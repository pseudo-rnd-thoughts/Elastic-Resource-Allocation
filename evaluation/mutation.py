"""
Evaluating the effect of task mutation on the results of the DIA and greedy algorithms

This is done in two parts; one investigating worsening of any task attributes and the second to investigate increasing
the value of a task for the case of military tactical networks.
"""

from __future__ import annotations

import json
import os
import pprint
import random as rnd
from typing import TYPE_CHECKING, Iterable

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


# noinspection DuplicatedCode
def full_task_mutation(model_dist: ModelDistribution, repeat_num: int, repeats: int = 25, time_limit: int = 2,
                       price_change: int = 3, initial_price: int = 25,
                       model_mutations: int = 15, mutate_percent: float = 0.15):
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
        to_mutate_tasks = [task for task, allocated in allocated_tasks.items()]  # if allocated todo future testing
        reset_model(tasks, servers)

        # Loop each time mutating a task or server and find the auction results and compare to the unmutated result
        for model_mutation in range(min(model_mutations, len(to_mutate_tasks))):
            # Choice a random task and mutate it
            task: Task = to_mutate_tasks.pop(rnd.randint(0, len(to_mutate_tasks) - 1))
            mutant_task = task.mutate(mutate_percent)

            # Replace the task with the mutant task in the task list
            list_item_replacement(tasks, task, mutant_task)
            assert mutant_task in tasks
            assert task not in tasks

            # Find the result with the mutated task
            mutant_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit)
            mutation_results[f'mutation {model_mutation}'] = mutant_result.store(**{
                'task price': task_prices[task], 'task allocated': allocated_tasks[task],
                'mutant price': mutant_task.price, 'mutant task allocated': mutant_task.running_server is not None,
                'mutant task name': task.name, 'mutant task deadline': mutant_task.deadline,
                'mutant task value': mutant_task.value, 'mutant task storage': mutant_task.required_storage,
                'mutant task computation': mutant_task.required_computation,
                'mutant task results data': mutant_task.required_results_data,
            })
            pp.pprint(mutation_results[f'mutation {model_mutation}'])

            # Replace the mutant task with the task in the task list
            list_item_replacement(tasks, mutant_task, task)
            assert mutant_task not in tasks
            assert task in tasks

        # Append the results to the data list
        model_results.append(mutation_results)

        # Save all of the results to a file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


def mutation_grid_search(model_dist: ModelDistribution, repeat_num: int, percent: float = 0.10,
                         time_limit: int = 3, price_change: int = 3, initial_price: int = 30):
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
    task = next(task for task in tasks if task.running_server is not None)
    mutation_results['no mutation'] = no_mutation_dia.store(**{'allocated': task.running_server is not None,
                                                               'task price': task.price})

    # The original task not mutated that is randomly selected (given the tasks are already randomly generated)
    permutations = ((int(task.required_storage * positive_percent) + 1) - task.required_storage) * \
                   ((int(task.required_computation * positive_percent) + 1) - task.required_computation) * \
                   ((int(task.required_results_data * positive_percent) + 1) - task.required_results_data) * \
                   ((task.deadline + 1) - int(task.deadline * negative_percent))
    print(f'Number of permutations: {permutations}, original solve time: {no_mutation_dia.solve_time}, '
          f'estimated time: {round(permutations * no_mutation_dia.solve_time / 60, 1)} minutes')
    reset_model(tasks, servers)
    mutation_pos = 0
    # Loop over all of the permutations that the task requirement resources have up to the mutate percentage
    for required_storage in range(task.required_storage, int(task.required_storage * positive_percent) + 1):
        for required_computation in range(task.required_computation,
                                          int(task.required_computation * positive_percent) + 1):
            for required_results_data in range(task.required_results_data,
                                               int(task.required_results_data * positive_percent) + 1):
                for deadline in range(int(task.deadline * negative_percent), task.deadline + 1):
                    # Create the new mutated task and create new tasks list with the mutant task replacing the task
                    mutant_task = Task(f'mutated {task.name}', required_storage=required_storage,
                                       required_computation=required_computation,
                                       required_results_data=required_results_data, deadline=deadline, value=task.value)
                    tasks.append(mutant_task)

                    # Calculate the task price with the mutated task
                    mutated_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit)
                    mutated_result.pretty_print()
                    mutation_results[f'Mutation {mutation_pos}'] = mutated_result.store(**{
                        'mutated task': task.name, 'task price': mutant_task.price,
                        'required storage': required_storage, 'required computation': required_computation,
                        'required results data': required_results_data, 'deadline': deadline,
                        'allocated': mutant_task.running_server is not None
                    })
                    mutation_pos += 1

                    # Remove the mutant task and read the task to the list of tasks and reset the model
                    tasks.remove(mutant_task)
                    reset_model(tasks, servers)

                    # Save all of the results to a file
                    with open(filename, 'w') as file:
                        json.dump(mutation_results, file)
    print('Finished running')


# noinspection DuplicatedCode
def value_only_mutation(model_dist: ModelDistribution, repeat_num: int, repeats: int = 25, time_limit: int = 2,
                        price_change: int = 3, initial_price: int = 25, model_mutations: int = 15,
                        value_mutations: Iterable[int] = (1, 2, 3, 4)):
    """
    Evaluates the value only mutation of tasks

    :param model_dist: Model distribution to generate tasks and servers
    :param repeat_num: The repeat number for saving the data
    :param repeats: The number of model repeats
    :param time_limit: DIA time limit
    :param price_change: Server price change
    :param initial_price: Server initial price
    :param model_mutations: The number of model mutation attempts
    :param value_mutations: The value difference to do testing with
    """
    print(f'Evaluates the value mutation of tasks')
    model_results = []
    pp = pprint.PrettyPrinter()
    filename = results_filename('value_mutation', model_dist, repeat_num)

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
        to_mutate_tasks = tasks[:]
        reset_model(tasks, servers)

        # Loop each time mutating a task or server and find the auction results and compare to the unmutated result
        for model_mutation in range(min(model_mutations, len(to_mutate_tasks))):
            # Choice a random task and mutate it
            task: Task = to_mutate_tasks.pop(rnd.randint(0, len(to_mutate_tasks) - 1))
            task_value = task.value

            task_mutation_results = {}
            for value in value_mutations:
                task.value = task_value - value

                # Find the result with the mutated task
                mutant_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit)
                task_mutation_results[f'value {value}'] = mutant_result.store(**{
                    'price': task.price, 'allocated': task.running_server is not None, 'value': task.value
                })
                pp.pprint(task_mutation_results[f'value {value}'])
                reset_model(tasks, servers)

            task.value = task_value
            mutation_results[f'task {task.name}'] = task_mutation_results

        # Append the results to the data list
        model_results.append(mutation_results)

        # Save all of the results to a file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


# noinspection DuplicatedCode
def dia_repeat(model_dist: ModelDistribution, repeat_num: int, repeats: int = 25, auction_repeats: int = 5,
               time_limit: int = 2, price_change: int = 3, initial_price: int = 25):
    """
    Tests the Decentralised iterative auction by repeating the auction to see if the same local / global maxima is
        achieved

    :param model_dist: The model distribution
    :param repeat_num: The repeat number
    :param repeats: The number of repeats
    :param auction_repeats: The number of auction repeats
    :param time_limit: The auction time limit
    :param price_change: Price change
    :param initial_price: The initial price
    """
    print(f'Evaluation of DIA by repeating the auction')
    model_results = []
    pp = pprint.PrettyPrinter()
    filename = results_filename('repeat_dia', model_dist, repeat_num)

    for repeat in range(repeats):
        print(f'\nRepeat: {repeat}')
        tasks, servers = model_dist.generate()
        set_server_heuristics(servers, price_change=price_change, initial_price=initial_price)

        repeat_results = {'model': {
            'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
        }}
        pp.pprint(repeat_results)

        for auction_repeat in range(auction_repeats):
            reset_model(tasks, servers)
            auction_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit=time_limit)
            auction_result.pretty_print()
            repeat_results[f'repeat {auction_repeat}'] = auction_result.store()

        model_results.append(repeat_results)
        # Save all of the results to a file
        with open(filename, 'w') as file:
            json.dump(model_results, file)
    print('Finished running')


if __name__ == "__main__":
    args = parse_args()

    if args.extra == '' or args.extra == 'task mutation':
        full_task_mutation(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
    elif args.extra == 'mutation grid search':
        mutation_grid_search(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
    elif args.extra == 'value only':
        value_only_mutation(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
    elif args.extra == 'dia repeat':
        dia_repeat(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
    elif args.extra == 'special case':
        print(os.getcwd())
        dia_repeat(ModelDistribution('models/mutation_1.mdl'), args.repeat, repeats=0, auction_repeats=10)
        dia_repeat(ModelDistribution('models/mutation_2.mdl'), args.repeat, repeats=0, auction_repeats=10)
    else:
        raise Exception(f'Unknown extra argument: {args.extra}')
