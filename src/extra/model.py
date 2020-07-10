"""
Model distribution
"""

from __future__ import annotations

import json
import random as rnd
from typing import TYPE_CHECKING

from src.core.server import Server
from src.core.task import Task

if TYPE_CHECKING:
    from typing import Tuple, List, Optional


class ModelDistribution:
    """Model distributions"""

    def __init__(self, dist_file: str, num_tasks: Optional[int] = None, num_servers: Optional[int] = None):
        self.file = dist_file
        self.num_tasks = num_tasks
        self.num_servers = num_servers

        with open(self.file) as file:
            self.model_data = json.load(file)

            self.name: str = self.model_data['name']

    def generate(self) -> Tuple[List[Task], List[Server]]:
        """
        Creates a list of tasks and servers from a task and server distribution

        :return: A list of tasks and list of servers
        """
        return self.generate_tasks(), self.generate_servers()

    def generate_online(self, time_steps: int, mean_arrival_rate: int,
                        std_arrival_rate: float) -> Tuple[List[Task], List[Server]]:
        """
        Create a list of tasks and servers from a task and server distribution with online distribution

        :param time_steps: Number of time steps
        :param mean_arrival_rate: Mean number of tasks that arrive each time steps
        :param std_arrival_rate: Standard deviation of the number of tasks that arrive each time steps
        :return: A list of tasks and list of servers
        """
        tasks, task_id = [], 0
        for time_step in range(time_steps):
            for _ in range(max(1, int(rnd.gauss(mean_arrival_rate, std_arrival_rate)))):
                task = self.generate_rnd_task(task_id)
                task.auction_time, task_id = time_step, task_id + 1
                tasks.append(task)

        return tasks, self.generate_servers()

    def generate_tasks(self) -> List[Task]:
        """
        Generate a list of tasks from the model data

        :return: A list of tasks
        """
        if 'task distributions' in self.model_data:
            assert self.num_tasks is not None
            return [self.generate_rnd_task(task_id) for task_id in range(self.num_tasks)]
        else:
            return [Task.load(task_model) for task_model in self.model_data['tasks']]

    def generate_rnd_task(self, task_id) -> Task:
        """
        Generate a new random task using a task id

        :param task_id: The task id
        :return: A new random task
        """
        probability = rnd.random()
        task_dist = next(task_dist for i, task_dist in enumerate(self.model_data['task distributions'])
                         if probability <= sum(self.model_data['task distributions'][j]['probability']
                                               for j in range(i + 1)))
        return Task.load_dist(task_dist, task_id)

    def generate_servers(self) -> List[Server]:
        """
        Generate a list of server from the model data

        :return: A list of servers
        """
        if 'server distributions' in self.model_data:
            assert self.num_servers is not None
            return [self.generate_rnd_server(server_id) for server_id in range(self.num_servers)]
        else:
            return [Server.load(server_model) for server_model in self.model_data['servers']]

    def generate_rnd_server(self, server_id) -> Server:
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
