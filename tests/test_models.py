"""
Test the model distribution files
"""

import json
import os
import random as rnd
import sys

import numpy as np

from core.fixed_task import FixedSumPowerSpeeds, FixedTask
from extra.io import parse_args
from extra.model import ModelDistribution
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import SumPercentage
from greedy.server_selection_policy import SumResources
from greedy.value_density import UtilityDeadlinePerResource
from online import generate_online_model_dist, batch_tasks
from optimal.fixed_optimal import fixed_optimal


def test_model_distribution():
    print()
    files = os.listdir('models/')
    for file in files:
        if file == "caroline.mdl":
            model_dist = ModelDistribution('models/caroline.mdl', num_tasks=2)

            tasks, servers = model_dist.generate()
            assert len(tasks) == 2
            assert len(servers) == 8
        else:
            model_dist = ModelDistribution(f'models/{file}', num_tasks=4, num_servers=3)

            tasks, servers = model_dist.generate()
            assert len(tasks) == 4
            assert len(servers) == 3


def test_model_probability():
    print()
    with open('models/basic.mdl') as file:
        file_data = json.load(file)

        task_probabilities = [task_distribution['probability'] for task_distribution in file_data['task distributions']]
        print(f'Task Probabilities: [{" ".join([str(prob) for prob in task_probabilities])}]')
        print(f'Sum probabilities: [{" ".join([str(sum(task_probabilities[:p+1])) for p in range(len(task_probabilities))])}]')

        prob = rnd.random()
        print(f'Probability: {prob}')


def test_args():
    print()

    def eval_args(updated_args, model, tasks, servers, repeat):
        """
        Evaluates the arguments by updating the arguments and then testing the model, tasks, servers and repeat are
            equalled to the parsed arguments

        :param updated_args: List of updated args
        :param model: Value for the model location
        :param tasks: Value for the number of tasks
        :param servers: Value for the number of servers
        :param repeat: Value for the number of repeats
        """
        sys.argv = ['location'] + updated_args
        args = parse_args()
        assert args.model == model and args.tasks == tasks and args.servers == servers and args.repeat == repeat

    # Files
    eval_args(['--file', 'test'], 'models/test.mdl', None, None, 0)
    eval_args(['-f', 'test'], 'models/test.mdl', None, None, 0)

    # Tasks
    eval_args(['--file', 'test', '--tasks', '1'], 'models/test.mdl', 1, None, 0)
    eval_args(['-f', 'test', '-t', '2'], 'models/test.mdl', 2, None, 0)

    # Servers
    eval_args(['--file', 'test', '--servers', '3'], 'models/test.mdl', None, 3, 0)
    eval_args(['-f', 'test', '-s', '4'], 'models/test.mdl', None, 4, 0)

    # Repeat
    eval_args(['--file', 'test', '--repeat', '5'], 'models/test.mdl', None, None, 5)
    eval_args(['-f', 'test', '-r', '6'], 'models/test.mdl', None, None, 6)

    # Full
    eval_args(['--file', 'test', '--tasks', '7', '--servers', '8', '--repeat', '9'], 'models/test.mdl', 7, 8, 9)
    eval_args(['-f', 'test', '-t', '10', '-s', '11', '-r', '12'], 'models/test.mdl', 10, 11, 12)


def test_caroline_model(model_file: str = 'models/caroline_oneshot.mdl'):
    print('\n\n\tGreedy algorithm')
    print(f'Num of Tasks | Percent Tasks | Percent Social Welfare | Storage usage | Comp usage | Bandwidth usage')
    for num_tasks in range(24, 60, 4):
        model = ModelDistribution(model_file, num_tasks=num_tasks)
        tasks, servers = model.generate()

        greedy_result = greedy_algorithm(tasks, servers, UtilityDeadlinePerResource(), SumResources(), SumPercentage())
        # noinspection PyTypeChecker
        print(f' {num_tasks:11} | {greedy_result.percentage_tasks_allocated:^13} | '
              f'{greedy_result.percentage_social_welfare:^22} | '
              f'{round(np.mean(list(greedy_result.server_storage_used.values())), 3):^13} | '
              f'{round(np.mean(list(greedy_result.server_computation_used.values())), 3):^10} | '
              f'{round(np.mean(list(greedy_result.server_bandwidth_used.values())), 3):10}')

    print('\n\tFixed Tasks')
    print(f'Num Tasks | Percent Tasks | Percent Social Welfare | Storage usage | Comp usage | Bandwidth usage')
    for num_tasks in (24, 28, 32, 36, 40, 44, 48):
        model = ModelDistribution(model_file, num_tasks=num_tasks)
        tasks, servers = model.generate()
        fixed_tasks = [FixedTask(task, FixedSumPowerSpeeds()) for task in tasks]
        fixed_optimal_result = fixed_optimal(fixed_tasks, servers, 3)

        # noinspection PyTypeChecker
        print(f' {num_tasks:8} | {fixed_optimal_result.percentage_tasks_allocated:^13} | '
              f'{fixed_optimal_result.percentage_social_welfare:^22} | '
              f'{round(np.mean(list(fixed_optimal_result.server_storage_used.values())), 3):^13} | '
              f'{round(np.mean(list(fixed_optimal_result.server_computation_used.values())), 3):^10} | '
              f'{round(np.mean(list(fixed_optimal_result.server_bandwidth_used.values())), 3):10}')


def test_online_model_generation():
    print('')
    model = ModelDistribution('models/caroline_online.mdl')
    time_steps = 200
    tasks, servers = generate_online_model_dist(model, time_steps, 2, 4)

    for batch_length in (1, 2, 4, 5, 10):
        batched_tasks = batch_tasks(tasks, batch_length, time_steps)
        assert len(batched_tasks) == time_steps // batch_length
        print(f'Batch lengths: {", ".join([f"{time_step}: {len(batched_tasks[time_step])}" for time_step in range(0, time_steps // batch_length)])}')


def test_convert_online_oneshot():
    print()
    model = ModelDistribution('models/caroline_online.mdl', num_tasks=0)
    tasks, servers = model.generate()

    for server in servers:
        server.computation_capacity *= 2
        server.bandwidth_capacity *= 2

    print(f'[{", ".join([server.save() for server in servers])}]')


if __name__ == "__main__":
    # PYTHONPATH=./src/ python3 tests/test_models.py -f='caroline' -t='28' -s='', -r='0' -e='test message'
    loaded_args = parse_args()
    print(f'Model file: {loaded_args.file}, tasks: {loaded_args.tasks}, servers: {loaded_args.servers}, '
          f'repeat: {loaded_args.repeat}, extra: "{loaded_args.extra}"')

    loaded_model_dist = ModelDistribution(loaded_args.file, loaded_args.tasks, loaded_args.servers)
    if loaded_args.extra == 'test message':
        print('success')
    else:
        print('failure')
