"""Result from the greedy algorithm"""

from __future__ import annotations

import pprint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Literal

    from src.core.server import Server
    from src.core.elastic_task import ElasticTask


def resource_usage(server: Server, resource: Literal['storage', 'computation', 'bandwidth']) -> float:
    """
    Percentage usage by the server of a particular resource

    :param server: The server for which the particular resource usage is calculated for
    :param resource: One of the resources in the server
    :return: The percentage resource usage by the server
    """
    return round(1 - getattr(server, f'available_{resource}') / getattr(server, f'{resource}_capacity'), 3)


class Result:
    """
    Results class that holds information about the results of an algorithm
    """

    pp = pprint.PrettyPrinter()

    def __init__(self, algorithm_name: str, tasks: List[ElasticTask], servers: List[Server], solve_time: float,
                 limited: bool = False, is_auction: bool = False, **kwargs):
        self.data = {
            # General properties
            'algorithm': algorithm_name,
            'solve time': round(solve_time, 3)
        }

        if len(tasks):
            self.data.update({
                'social welfare': sum(task.value for task in tasks if task.running_server is not None),
                'social welfare percent': round(sum(task.value for task in tasks if task.running_server is not None) /
                                                sum(task.value for task in tasks), 3),
                'percentage tasks allocated': round(sum(1 for task in tasks if task.running_server) / len(tasks), 3)
            })
        else:
            self.data.update({'social welfare': 0, 'social welfare percent': 0, 'percentage tasks allocated': 0})

        if not limited:
            # Server properties
            self.data.update({
                'task resource usage': {
                    task.name: (task.loading_speed, task.compute_speed, task.sending_speed, task.running_server.name)
                    for task in tasks if task.running_server
                },
                'server storage usage': {
                    server.name: 1 - server.available_storage / server.storage_capacity for server in servers
                },
                'server compute usage': {
                    server.name: 1 - server.available_computation / server.computation_capacity for server in servers
                },
                'server bandwidth usage': {
                    server.name: 1 - server.available_bandwidth / server.bandwidth_capacity for server in servers
                },
                'server num tasks allocated': {
                    server.name: len(server.allocated_tasks) for server in servers
                }
            })

        if is_auction:
            # Auction properties
            self.data.update({
                'total revenue': sum(task.price for server in servers for task in server.allocated_tasks),
                'task prices': {task.name: task.price for server in servers for task in server.allocated_tasks},
                'server revenue': {server.name: server.revenue for server in servers},
            })

        self.data.update(kwargs)

    def pretty_print(self):
        """
        Pretty prints the results
        """
        self.pp.pprint(self.data)

    def store(self, **kwargs):
        """
        Returns the results values for storage

        :return: The results values
        """
        self.data.update(kwargs)

        return self.data

    @property
    def algorithm(self):
        """Algorithm property"""
        return self.data['algorithm']

    @property
    def social_welfare(self):
        """Social welfare property"""
        return self.data['social welfare']

    @property
    def solve_time(self):
        """Solve time property"""
        return self.data['solve time']

    @property
    def percentage_social_welfare(self):
        """Percentage social welfare"""
        return self.data['social welfare percent']

    @property
    def percentage_tasks_allocated(self):
        """Percentage of task's allocated"""
        return self.data['percentage tasks allocated']

    @property
    def server_social_welfare(self):
        """Dictionary of server based social welfare"""
        return self.data['server social welfare']

    @property
    def server_storage_used(self):
        """Dictionary of server based storage used"""
        return self.data['server storage usage']

    @property
    def server_computation_used(self):
        """Dictionary of server based computational used"""
        return self.data['server compute usage']

    @property
    def server_bandwidth_used(self):
        """Dictionary of server based bandwidth used"""
        return self.data['server bandwidth usage']

    @property
    def server_num_tasks_allocated(self):
        """Dictionary of server based number of tasks allocated"""
        return self.data['server num tasks allocated']
