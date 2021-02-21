"""
Model distribution
"""

from __future__ import annotations

import json
import random as rnd
from math import ceil
from typing import TYPE_CHECKING

import pandas as pd

from src.core.server import Server
from src.core.task import Task

if TYPE_CHECKING:
    from typing import Tuple, List, Optional


class ModelDistribution:
    """Model distributions"""

    storage_scaling = 150
    computational_scaling = 0.5
    results_data_scaling = 1

    def __init__(self, filename: str, num_tasks: Optional[int] = None, num_servers: Optional[int] = None):
        self.filename = filename
        self.num_tasks = num_tasks
        self.num_servers = num_servers

        with open(self.filename) as file:
            self.model_data = json.load(file)

            self.name: str = self.model_data['name']
            if 'task filename' in self.model_data:
                model_path = '/'.join(filename.split('/')[:-1]) + '/' + self.model_data['task filename']
                self.task_model = pd.read_csv(model_path)
            else:
                self.task_model = None

    def generate(self) -> Tuple[List[Task], List[Server]]:
        """
        Creates a list of tasks and servers from a task and server distribution

        :return: A list of tasks and list of servers
        """
        servers = self.generate_servers()
        return self.generate_tasks(servers), servers

    def generate_online(self, time_steps: int, mean_arrival_rate: int,
                        std_arrival_rate: float) -> Tuple[List[Task], List[Server]]:
        """
        Create a list of tasks and servers from a task and server distribution with online distribution

        :param time_steps: Number of time steps
        :param mean_arrival_rate: Mean number of tasks that arrive each time steps
        :param std_arrival_rate: Standard deviation of the number of tasks that arrive each time steps
        :return: A list of tasks and list of servers
        """
        servers = self.generate_servers()

        tasks, task_id = [], 0
        for time_step in range(time_steps):
            for task in range(max(0, int(rnd.gauss(mean_arrival_rate, std_arrival_rate)))):
                if 'task distributions' in self.model_data:
                    task = self.generate_synthetic_task(task_id, servers)
                elif 'task filename' in self.model_data:
                    task = self.generate_alibaba_task(task_id, servers)
                else:
                    raise Exception('Unknown model type')

                task.auction_time, task_id = time_step, task_id + 1
                tasks.append(task)

        return tasks, servers

    def generate_tasks(self, servers: List[Server]) -> List[Task]:
        """
        Generate a list of tasks from the model data

        :param servers: List of servers
        :return: A list of tasks
        """
        if 'task distributions' in self.model_data:
            assert self.num_tasks is not None
            return [self.generate_synthetic_task(task_id, servers) for task_id in range(self.num_tasks)]
        elif 'task filename' in self.model_data:
            assert self.num_tasks is not None
            return [self.generate_alibaba_task(task_id, servers) for task_id in range(self.num_tasks)]
        else:
            return [Task.load(task_model) for task_model in self.model_data['tasks']]

    def generate_synthetic_task(self, task_id: int, servers: List[Server]) -> Task:
        """
        Generate a new synthetic task

        :param task_id: The task id
        :param servers: List of servers
        :return: A new random task
        """
        probability = rnd.random()
        task_dist = next(task_dist for i, task_dist in enumerate(self.model_data['task distributions'])
                         if probability <= sum(self.model_data['task distributions'][j]['probability']
                                               for j in range(i + 1)))
        return Task.load_dist(task_dist, task_id, servers)

    def generate_alibaba_task(self, task_id: int, servers: List[Server]) -> Task:
        """
        Generate a new alibaba task

        :param task_id: The task id
        :param servers: List of servers
        :return: A new random task
        """
        task_sample = self.task_model.sample()
        for index, task_row in task_sample.iterrows():
            return Task(f'realistic {task_id}',
                        required_storage=ceil(self.storage_scaling*task_row['mem_max']),
                        required_computation=ceil(self.computational_scaling*task_row['total_cpu']),
                        required_results_data=ceil(self.results_data_scaling*rnd.randint(20, 60) * task_row['mem_max']),
                        value=None, deadline=task_row['time_taken'], servers=servers,
                        planned_storage=ceil(self.storage_scaling*task_row['plan_mem']),
                        planned_computation=ceil(self.computational_scaling*task_row['plan_cpu']))

    def generate_servers(self) -> List[Server]:
        """
        Generate a list of server from the model data

        :return: A list of servers
        """
        if 'server distributions' in self.model_data:
            assert self.num_servers is not None
            return [self.generate_synthetic_server(server_id) for server_id in range(self.num_servers)]
        else:
            return [Server.load(server_model) for server_model in self.model_data['servers']]

    def generate_synthetic_server(self, server_id) -> Server:
        """
        Generate a new random serer using a server id

        :param server_id: The server id
        :return: A new random server
        """
        probability = rnd.random()
        server_dist = next(server_dist for i, server_dist in enumerate(self.model_data['server distributions'])
                           if probability <= sum(self.model_data['server distributions'][j]['probability']
                                                 for j in range(i + 1)))
        return Server.load_dist(server_dist, server_id)
