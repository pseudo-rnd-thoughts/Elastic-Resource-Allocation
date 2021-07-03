"""
Model distribution
"""

from __future__ import annotations

import json
import os
import random as rnd
from math import ceil
from pprint import PrettyPrinter
from typing import TYPE_CHECKING

import pandas as pd

from src.core.non_elastic_task import generate_non_elastic_tasks
from src.core.server import Server
from src.core.elastic_task import ElasticTask

if TYPE_CHECKING:
    from typing import Tuple, List, Optional


class ModelDist:
    def __init__(self, model_filename: Optional[str] = None, num_tasks: Optional[int] = None,
                 num_servers: Optional[int] = None):
        self.num_tasks = num_tasks
        self.num_servers = num_servers

        with open(model_filename) as file:
            self.model = json.load(file)

            self.name = self.model['name']

    def generate_oneshot(self) -> Tuple[List[ElasticTask], List[Server]]:
        """
        Creates a list of tasks and servers from a task and server distribution

        :return: A list of tasks and list of servers
        """
        servers = [self.generate_server(server_id) for server_id in range(self.num_servers)]
        return [self.generate_task(servers, task_id) for task_id in range(self.num_tasks)], servers

    def generate_online(self, time_steps: int, mean_arrival_rate: int,
                        std_arrival_rate: float) -> Tuple[List[ElasticTask], List[Server]]:
        """
        Create a list of tasks and servers from a task and server distribution with online distribution

        :param time_steps: Number of time steps
        :param mean_arrival_rate: Mean number of tasks that arrive each time steps
        :param std_arrival_rate: Standard deviation of the number of tasks that arrive each time steps
        :return: A list of tasks and list of servers
        """
        servers = [self.generate_server(server_id) for server_id in range(self.num_servers)]

        tasks, task_id = [], 0
        for time_step in range(time_steps):
            for task in range(max(0, int(rnd.gauss(mean_arrival_rate, std_arrival_rate)))):
                task = self.generate_task(servers, task_id)

                task.auction_time, task_id = time_step, task_id + 1
                tasks.append(task)

        return tasks, servers

    def generate_server(self, server_id: int) -> Server:
        return Server.load(self.model['servers'][server_id])

    def generate_task(self, servers: List[Server], task_id: int) -> ElasticTask:
        return ElasticTask.load(self.model['tasks'][task_id])


class SyntheticModelDist(ModelDist):
    def __init__(self, num_tasks: Optional[int] = None, num_servers: Optional[int] = None,
                 filename: str = 'models/synthetic.mdl'):
        ModelDist.__init__(self, filename, num_tasks, num_servers)

    def generate_server(self, server_id: int) -> Server:
        probability = rnd.random()
        server_dist = next(server_dist for i, server_dist in enumerate(self.model['server distributions'])
                           if probability <= sum(self.model['server distributions'][j]['probability']
                                                 for j in range(i + 1)))
        return Server.load_dist(server_dist, server_id)

    def generate_task(self, servers: List[Server], task_id: int) -> ElasticTask:
        probability = rnd.random()
        task_dist = next(task_dist for i, task_dist in enumerate(self.model['task distributions'])
                         if probability <= sum(self.model['task distributions'][j]['probability']
                                               for j in range(i + 1)))
        return ElasticTask.load_dist(task_dist, task_id)


class AlibabaModelDist(SyntheticModelDist):
    def __init__(self, num_tasks: Optional[int] = None, num_servers: Optional[int] = None, foreknowledge: bool = True,
                 filename: str = 'models/alibaba.mdl', storage_scaling: int = 1000, computational_scaling: int = 0.5,
                 results_data_scaling: int = 100, results_range: Tuple[int, int] = (20, 60)):
        SyntheticModelDist.__init__(self, num_tasks, num_servers, filename)

        self.foreknowledge = foreknowledge

        self.storage_scaling = storage_scaling
        self.computational_scaling = computational_scaling
        self.results_scaling = results_data_scaling

        self.results_range = results_range

        task_model_path = '/'.join(filename.split('/')[:-1]) + '/' + self.model['task filename']
        self.task_model = pd.read_csv(task_model_path)

    def generate_task(self, servers: List[Server], task_id: int) -> ElasticTask:
        for index, task_row in self.task_model.sample().iterrows():
            if self.foreknowledge:
                return ElasticTask(
                    f'Foreknowledge Task {task_id}',
                    required_storage=int(self.storage_scaling * task_row['mem-max']),
                    required_computation=int(self.computational_scaling * task_row['cpu-avg'] * task_row['time-taken']),
                    required_results_data=ceil(self.results_scaling * rnd.uniform(*self.results_range) *
                                               task_row['mem-max']),
                    deadline=task_row['time-taken'], servers=servers)
            else:
                return ElasticTask(
                    f'Requested Task {task_id}',
                    required_storage=int(self.storage_scaling * task_row['request-mem']),
                    required_computation=int(self.computational_scaling * task_row['request-cpu'] *
                                             task_row['time-taken']),
                    required_results_data=ceil(self.results_scaling * rnd.uniform(*self.results_range) *
                                               task_row['request-mem']),
                    deadline=task_row['time-taken'], servers=servers)

    def generate_foreknowledge_requested_tasks(self, servers: List[Server],
                                               num_tasks: int) -> Tuple[List[ElasticTask], List[ElasticTask]]:
        foreknowledge_tasks, requested_tasks = [], []
        for task_id, (_, task_row) in enumerate(self.task_model.sample(num_tasks).iterrows()):
            results_data_size = self.results_scaling * rnd.uniform(*self.results_range)
            foreknowledge_task = ElasticTask(
                f'Foreknowledge Task {task_id}',
                required_storage=int(self.storage_scaling * task_row['mem-max']),
                required_computation=int(self.computational_scaling * task_row['cpu-avg'] * task_row['time-taken']),
                required_results_data=ceil(results_data_size * task_row['mem-max']),
                deadline=task_row['time-taken'], servers=servers)
            requested_task = ElasticTask(
                f'Requested Task {task_id}',
                required_storage=int(self.storage_scaling * task_row['request-mem']),
                required_computation=int(self.computational_scaling * task_row['request-cpu'] * task_row['time-taken']),
                required_results_data=ceil(results_data_size * task_row['request-mem']),
                deadline=task_row['time-taken'], value=foreknowledge_task.value)

            foreknowledge_tasks.append(foreknowledge_task)
            requested_tasks.append(requested_task)
        return foreknowledge_tasks, requested_tasks


def get_model(model_name: str, num_tasks: Optional[int] = None, num_servers: Optional[int] = None) -> ModelDist:
    if model_name == 'alibaba':
        return AlibabaModelDist(num_tasks, num_servers)
    elif model_name == 'synthetic':
        return SyntheticModelDist(num_tasks, num_servers)
    else:
        if os.path.exists(model_name):
            return ModelDist(model_filename=model_name)
        else:
            raise Exception(f'Unknown model distribution ({model_name})')


def generate_evaluation_model(model_dist: ModelDist, pp: PrettyPrinter):
    # Generate the tasks and servers
    tasks, servers = model_dist.generate_oneshot()
    non_elastic_tasks = generate_non_elastic_tasks(tasks)
    algorithm_results = {'model': {
        'tasks': [task.save() for task in tasks], 'servers': [server.save() for server in servers]
    }}
    pp.pprint(algorithm_results)

    return tasks, servers, non_elastic_tasks, algorithm_results
