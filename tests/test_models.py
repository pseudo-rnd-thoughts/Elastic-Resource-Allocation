"""
Test the model distribution files
"""
import json
import os
import random as rnd
import sys
from math import ceil

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.core.core import reset_model
from src.core.non_elastic_task import NonElasticTask, SumSpeedPowResourcePriority
from src.core.elastic_task import ElasticTask
from src.extra.io import parse_args
from src.extra.model import AlibabaModelDist, SyntheticModelDist, ModelDist
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation import SumPercentage
from src.greedy.server_selection import SumResources
from src.greedy.task_priority import UtilityDeadlinePerResourcePriority
from src.optimal.non_elastic_optimal import non_elastic_optimal


def test_models():
    synthetic_model = SyntheticModelDist(10, 10)
    synthetic_model.generate_oneshot()
    synthetic_model.generate_online(100, 1, 0.5)

    alibaba_model = AlibabaModelDist(10, 10)
    alibaba_model.generate_oneshot()
    alibaba_model.generate_online(100, 1, 0.5)

    tasks, servers = synthetic_model.generate_oneshot()
    with open('test.mdl', 'w') as file:
        json.dump({'name': 'test model', 'servers': [server.save() for server in servers],
                   'tasks': [task.save() for task in tasks]}, file)
    ModelDist('test.mdl', 10, 10)
    os.remove('test.mdl')


def alibaba_task_generation():
    """
    Tests if the task generation for the alibaba dataset is valid
    """
    print()

    model_dist = AlibabaModelDist(num_tasks=10, num_servers=4)
    servers = [model_dist.generate_server(server_id) for server_id in range(model_dist.num_servers)]
    alibaba = pd.read_csv('../models/alibaba_cluster_tasks.csv')
    storage_scaling, computational_scaling, results_data_scaling = 500, 1, 5
    non_elastic_task_policy = SumSpeedPowResourcePriority()

    for index, task_row in tqdm(alibaba.iterrows()):
        task = ElasticTask(f'realistic {index}',
                           required_storage=ceil(storage_scaling * min(task_row['mem_max'], task_row['plan_mem'])),
                           required_computation=ceil(computational_scaling * task_row['total_cpu']),
                           required_results_data=ceil(results_data_scaling * rnd.randint(20, 60) * task_row['mem_max']),
                           deadline=task_row['time_taken'], servers=servers)
        try:
            NonElasticTask(task, non_elastic_task_policy)
        except AssertionError as e:
            print(f'Error for fixed task index {index}', e)
            print(task.required_storage / storage_scaling, task.required_computation / computational_scaling,
                  task.required_results_data / results_data_scaling)


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
        assert args.model == model and args.tasks == tasks and args.servers == servers and args.repeat == repeat, \
            f'Expects: {args.model}, {args.tasks}, {args.servers}, {args.repeat}, ' \
            f'actual: {model}, {tasks}, {servers}, {repeat}'

    # Files
    eval_args(['--model', 'test'], 'test', None, None, 0)
    eval_args(['-m', 'test'], 'test', None, None, 0)

    # Tasks
    eval_args(['--model', 'test', '--tasks', '1'], 'test', 1, None, 0)
    eval_args(['-m', 'test', '-t', '2'], 'test', 2, None, 0)

    # Servers
    eval_args(['--model', 'test', '--servers', '3'], 'test', None, 3, 0)
    eval_args(['-m', 'test', '-s', '4'], 'test', None, 4, 0)

    # Repeat
    eval_args(['--model', 'test', '--repeat', '5'], 'test', None, None, 5)
    eval_args(['-m', 'test', '-r', '6'], 'test', None, None, 6)

    # full
    eval_args(['--model', 'test', '--tasks', '7', '--servers', '8', '--repeat', '9'], 'test', 7, 8, 9)
    eval_args(['-m', 'test', '-t', '10', '-s', '11', '-r', '12'], 'test', 10, 11, 12)


def test_model_tasks(num_servers: int = 8):
    greedy_results = []
    fixed_results = []
    for num_tasks in range(24, 60, 4):
        model = SyntheticModelDist(num_tasks, num_servers)
        tasks, servers = model.generate_oneshot()
        fixed_tasks = [NonElasticTask(task, SumSpeedPowResourcePriority()) for task in tasks]

        greedy_results.append([num_tasks, greedy_algorithm(tasks, servers, UtilityDeadlinePerResourcePriority(),
                                                           SumResources(), SumPercentage())])
        reset_model(tasks, servers)
        fixed_results.append([num_tasks, non_elastic_optimal(fixed_tasks, servers, 3)])

    def print_results(results):
        """
        Print the results of an algorithm

        :param results: List of results
        """
        print(f'Num of Tasks | Percent Tasks | Social Welfare % | Storage usage | Comp usage | Bandwidth usage')
        for task_num, result in results:
            # noinspection PyTypeChecker
            print(f' {task_num:11} | {result.percentage_tasks_allocated:^13} | '
                  f'{result.percentage_social_welfare:^22} | '
                  f'{round(np.mean(list(result.server_storage_used.values())), 3):^13} | '
                  f'{round(np.mean(list(result.server_computation_used.values())), 3):^10} | '
                  f'{round(np.mean(list(result.server_bandwidth_used.values())), 3):10}')

    print('\n\n\tGreedy algorithm')
    print_results(greedy_results)
    print('\n\tFixed Tasks')
    print_results(fixed_results)

    print(f'\nNum of Tasks | Difference | Greedy SW | Fixed SW')
    for (num_tasks, greedy_result), (_, fixed_result) in zip(greedy_results, fixed_results):
        print(f' {num_tasks:11} | {fixed_result.social_welfare - greedy_result.social_welfare:10.3f} | '
              f'{greedy_result.social_welfare:9.3f} | {fixed_result.social_welfare:8.3f}')


if __name__ == "__main__":
    alibaba_task_generation()
