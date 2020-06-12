"""This creates the models for the tasks and servers"""

from __future__ import annotations

import json
from random import gauss, random
from typing import List, Tuple, Dict, Union

from core.task import Task
from core.server import Server


def positive_gaussian_dist(mean, std) -> int:
    """
    Uses gaussian distribution to generate a random number greater than 0 for a resource
    :param mean: Gaussian mean
    :param std: Gaussian standard deviation
    :return: A float of random gaussian distribution
    """
    return max(1, int(gauss(mean, std)))


class JobDist(object):
    """
    Random task distribution using gaussian (normal distribution)
    """

    def __init__(self, dist_name, probability,
                 storage_mean, storage_std,
                 computation_mean, computation_std,
                 results_data_mean, results_data_std,
                 value_mean, value_std,
                 deadline_mean, deadline_std):
        self.dist_name = dist_name
        self.probability = probability
        self.storage_mean = storage_mean
        self.storage_std = storage_std
        self.computation_mean = computation_mean
        self.computation_std = computation_std
        self.results_data_mean = results_data_mean
        self.results_data_std = results_data_std
        self.value_mean = value_mean
        self.value_std = value_std
        self.deadline_mean = deadline_mean
        self.deadline_std = deadline_std

    def create_task(self, name) -> Task:
        """
        Creates a new task with name (unique identifier)
        :param name: The name of the task
        :return: A new task object
        """
        task_name = "{} {}".format(self.dist_name, name)
        return Task(name=task_name,
                    required_storage=positive_gaussian_dist(self.storage_mean, self.storage_std),
                    required_computation=positive_gaussian_dist(self.computation_mean, self.computation_std),
                    required_results_data=positive_gaussian_dist(self.results_data_mean, self.results_data_std),
                    value=positive_gaussian_dist(self.value_mean, self.value_std),
                    deadline=int(positive_gaussian_dist(self.deadline_mean, self.deadline_std)))

    def save(self) -> Dict[str, Union[str, int]]:
        """
        Save the task dist
        :return: The Json code for the task dist
        """
        return {
            "name": self.dist_name,
            "probability": self.probability,
            "required_storage_mean": self.storage_mean,
            "required_storage_std": self.storage_std,
            "required_computation_mean": self.computation_mean,
            "required_computation_std": self.computation_std,
            "required_results_data_mean": self.results_data_mean,
            "required_results_data_std": self.results_data_std,
            "value_mean": self.value_mean,
            "value_std": self.value_std,
            "deadline_mean": self.deadline_mean,
            "deadline_std": self.deadline_std
        }


class ServerDist(object):
    """
    Random server distribution using gaussian (normal distribution)
    """

    def __init__(self, dist_name, probability,
                 storage_mean, storage_std,
                 computation_mean, computation_std,
                 results_data_mean, results_data_std):
        self.dist_name = dist_name
        self.probability = probability
        self.storage_mean = storage_mean
        self.storage_std = storage_std
        self.computation_mean = computation_mean
        self.computation_std = computation_std
        self.results_data_mean = results_data_mean
        self.results_data_std = results_data_std

    def create_server(self, name) -> Server:
        """
        Creates a new server with name (unique identifier)
        :param name: The name of the server
        :return: A new task object
        """
        server_name = "{} {}".format(self.dist_name, name)
        return Server(name=server_name,
                      storage_capacity=positive_gaussian_dist(self.storage_mean, self.storage_std),
                      computation_capacity=positive_gaussian_dist(self.computation_mean, self.computation_std),
                      bandwidth_capacity=positive_gaussian_dist(self.results_data_mean, self.results_data_std))

    def save(self) -> Dict[str, Union[str, int]]:
        """
        Save the server dist
        :return: The Json code for the server dist
        """
        return {
            "name": self.dist_name,
            "probability": self.probability,
            "maximum_storage_mean": self.storage_mean,
            "maximum_storage_std": self.storage_std,
            "maximum_computation_mean": self.computation_mean,
            "maximum_computation_std": self.computation_std,
            "maximum_bandwidth_mean": self.results_data_mean,
            "maximum_bandwidth_std": self.results_data_std
        }


class ModelDist(object):
    """Model distributions"""
    num_tasks = 0
    num_servers = 0

    def __init__(self, dist_name: str, task_dists: List[JobDist], num_tasks: int,
                 server_dists: List[ServerDist], num_servers: int):
        self.file_name = "{}_j{}_s{}".format(dist_name, num_tasks, num_servers)
        self.dist_name = dist_name

        self.task_dists = task_dists
        self.num_tasks = num_tasks
        self.server_dists = server_dists
        self.num_servers = num_servers

    def create(self) -> Tuple[List[Task], List[Server]]:
        """
        Creates a list of tasks and servers from a task and server distribution
        :return: A list of tasks and list of servers
        """
        tasks: List[Task] = []
        for task_pos in range(self.num_tasks):
            prob = random()
            for task_dist in self.task_dists:
                if prob < task_dist.probability:
                    tasks.append(task_dist.create_task(task_pos))
                    break
                else:
                    prob -= task_dist.probability

        servers: List[Server] = []
        for server_pos in range(self.num_servers):
            prob = random()
            for server_dist in self.server_dists:
                if prob < server_dist.probability:
                    servers.append(server_dist.create_server(server_pos))
                    break
                else:
                    prob -= server_dist.probability

        return tasks, servers


def load_dist(filename: str) -> Tuple[str, List[JobDist], List[ServerDist]]:
    """
    Loads tasks and server distributions from a file
    :param filename: The filename to load from
    :return: A tuple of the list of random task distributions and random server distributions
    """

    with open(filename) as file:
        data = json.load(file)

        task_dists: List[JobDist] = [
            JobDist(dist['name'], dist['probability'],
                    dist['required_storage_mean'], dist['required_storage_std'],
                    dist['required_computation_mean'], dist['required_computation_std'],
                    dist['required_results_data_mean'], dist['required_results_data_std'],
                    dist['value_mean'], dist['value_std'],
                    dist['deadline_mean'], dist['deadline_std'])
            for dist in data['task_dist']
        ]

        server_dists: List[ServerDist] = [
            ServerDist(dist['name'], dist['probability'],
                       dist['maximum_storage_mean'], dist['maximum_storage_std'],
                       dist['maximum_computation_mean'], dist['maximum_computation_std'],
                       dist['maximum_bandwidth_mean'], dist['maximum_bandwidth_std'])
            for dist in data['server_dist']
        ]

        return data['name'], task_dists, server_dists


def reset_model(tasks: List[Task], servers: List[Server], forgot_price: bool = True):
    """
    Resets all of the tasks and servers back after an allocation
    :param tasks: A list of tasks
    :param servers: A list of servers
    :param forgot_price: If to forgot the task price
    """
    for task in tasks:
        task.reset_allocation(forgot_price=forgot_price)

    for server in servers:
        server.reset_allocations()
