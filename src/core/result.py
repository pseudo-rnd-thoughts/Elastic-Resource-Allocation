"""Result from the greedy algorithm"""

from __future__ import annotations

from typing import List

from core.task import Task
from core.server import Server


class Result(object):
    """Generic results class"""

    def __init__(self, algorithm_name: str, tasks: List[Task], servers: List[Server], solve_time: float,
                 show_money: bool = False, **kwargs):
        self.algorithm_name = algorithm_name

        self.data = dict()
        self.data['solve_time'] = round(solve_time, 3)

        # General total information
        self.sum_value = sum(sum(task.value for task in server.allocated_tasks) for server in servers)
        self.data['sum value'] = self.sum_value
        self.data['percentage value'] = round(sum(task.value for task in tasks if task.running_server) /
                                              sum(task.value for task in tasks), 3)
        self.data['percentage tasks'] = round(sum(1 for task in tasks if task.running_server) / len(tasks), 3)

        # The server information
        self.data['server value'] = {
            server.name: sum(task.value for task in server.allocated_tasks) for server in servers
        }
        self.data['server storage usage'] = {
            server.name: round(1 - server.available_storage / server.storage_capacity, 3) for server in servers
        }
        self.data['server computation usage'] = {
            server.name: round(1 - server.available_computation / server.computation_capacity, 3) for server in servers
        }
        self.data['server bandwidth usage'] = {
            server.name: round(1 - server.available_bandwidth / server.bandwidth_capacity, 3) for server in servers
        }
        self.data['num tasks'] = {
            server.name: len(server.allocated_tasks) for server in servers
        }

        # Additional information
        for key, value in kwargs.items():
            self.data[key] = value

        # For auction to add the price information
        if show_money:
            self.data['total money'] = sum(task.price for task in tasks)
            self.data['prices'] = {task.name: task.price for task in tasks}
            self.data['revenues'] = {server.name: server.revenue for server in servers}
            self.data['price change'] = {server.name: server.price_change for server in servers}

    def store(self, **kwargs):
        """
        Returns the results values for storage
        :return: The results values
        """
        for key, value in kwargs.items():
            self.data[key] = value
        return self.data
