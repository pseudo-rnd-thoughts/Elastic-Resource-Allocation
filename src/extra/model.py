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
            model_data = json.load(file)

            self.name: str = model_data['name']
            if num_tasks is not None:
                assert 'task distributions' in model_data
            else:
                assert 'tasks' in model_data

            if num_servers is not None:
                assert 'server distributions' in model_data
            else:
                assert 'servers' in model_data

    def generate(self) -> Tuple[List[Task], List[Server]]:
        """
        Creates a list of tasks and servers from a task and server distribution

        :return: A list of tasks and list of servers
        """
        with open(self.file) as file:
            model_data = json.load(file)

            if 'task distributions' in model_data:
                tasks = []
                for pos in range(self.num_tasks):
                    probability = rnd.random()
                    task_dist = next(task_dist for i, task_dist in enumerate(model_data['task distributions'])
                                     if probability <= sum(model_data['task distributions'][j]['probability']
                                                           for j in range(i + 1)))
                    tasks.append(Task.load_dist(task_dist, pos))
            else:
                tasks = [Task.load(task_model) for task_model in model_data['tasks']]

            if 'server distributions' in model_data:
                servers = []
                for pos in range(self.num_servers):
                    probability = rnd.random()
                    server_dist = next(server_dist for i, server_dist in enumerate(model_data['server distributions'])
                                       if probability <= sum(model_data['server distributions'][j]['probability']
                                                             for j in range(i + 1)))
                    servers.append(Server.load_dist(server_dist, pos))
            else:
                servers = [Server.load(server_model) for server_model in model_data['servers']]

            return tasks, servers


def results_filename(test_name: str, model_dist: ModelDistribution, repeat: int = None) -> str:
    """
    Generates the save filename for testing results

    :param test_name: The test name
    :param model_dist: The model distribution
    :param repeat: The repeat number
    :return: The concatenation of the test name, model distribution name and the repeat
    """
    date = dt.datetime.now().strftime("%m-%d_%H-%M-%S")
    if repeat is None:
        return f'{test_name}_{model_dist.name}_{date}.json'
    else:
        return f'{test_name}_{model_dist.name}_{repeat}_{date}.json'
