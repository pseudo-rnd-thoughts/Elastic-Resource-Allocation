"""
Model distribution
"""

from __future__ import annotations

import datetime as dt
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

    def generate_tasks(self) -> List[Task]:
        """
        Generate a list of tasks from the model data

        :return: A list of tasks
        """
        if 'task distributions' in self.model_data:
            return [self.generate_rnd_task(task_id) for task_id in range(self.num_tasks)]
        else:
            return [Task.load(task_model) for task_model in self.model_data['tasks']]

    def generate_servers(self) -> List[Server]:
        """
        Generate a list of server from the model data

        :return: A list of servers
        """
        if 'server distributions' in self.model_data:
            return [self.generate_rnd_server(server_id) for server_id in range(self.num_servers)]
        else:
            return [Server.load(server_model) for server_model in self.model_data['servers']]

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


def results_filename(test_name: str, model_dist: ModelDistribution, repeat: int = None, save_date: bool = False) -> str:
    """
    Generates the save filename for testing results

    :param test_name: The test name
    :param model_dist: The model distribution
    :param repeat: The repeat number
    :param save_date: If to save the date
    :return: The concatenation of the test name, model distribution name and the repeat
    """
    extra_info = f'_{model_dist.num_tasks}' if model_dist.num_tasks else '' + \
        f'_{model_dist.num_servers}' if model_dist.num_servers else '' + \
        f'_{dt.datetime.now().strftime("%m-%d_%H-%M-%S")}' if save_date else ''
    if repeat is None or repeat == 0:
        return f'{test_name}_{model_dist.name}{extra_info}.json'
    else:
        return f'{test_name}_{model_dist.name}_{repeat}{extra_info}.json'
