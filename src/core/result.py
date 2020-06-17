"""Result from the greedy algorithm"""

from __future__ import annotations

import pprint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List

    from core.server import Server
    from core.task import Task


class Result:
    """
    Results class that holds information about the results of an algorithm
    """

    def __init__(self, algorithm_name: str, tasks: List[Task], servers: List[Server], solve_time: float,
                 limited: bool = False, is_auction: bool = False, **kwargs):
        self.data = {
            # General properties
            'algorithm': algorithm_name,
            'solve time': round(solve_time, 3),
            'social welfare': sum(task.value for server in servers for task in server.allocated_tasks),
            'percentage task value allocated': round(sum(task.value for task in tasks if task.running_server) /
                                                     sum(task.value for task in tasks), 3),
            'percentage tasks allocated': round(sum(1 for task in tasks if task.running_server) / len(tasks), 3)
        }

        if limited:
            # Server properties
            def resource_usage(server, resource):
                """Resource usage of a server with a particular resource"""
                return round(1 - getattr(server, f'available_{resource}') / getattr(server, f'{resource}_capacity'), 3)

            self.data.update({
                'server social welfare': {server.name: sum(task.value for task in server.allocated_tasks)
                                          for server in servers},
                'server storage usage': {server.name: resource_usage(server, 'storage') for server in servers},
                'server computation usage': {server.name: resource_usage(server, 'computation') for server in servers},
                'server bandwidth usage': {server.name: resource_usage(server, 'bandwidth') for server in servers},
                'server allocated tasks': {server.name: len(server.allocated_tasks) for server in servers}
            })

        if is_auction:
            # Auction properties
            self.data.update({
                'revenue': sum(task.price for server in servers for task in server.allocated_tasks),
                'task prices': {task.name: task.price for server in servers for task in server.allocated_tasks},
                'server revenue': {server.name: server.revenue for server in servers},
            })

        self.data.update(kwargs)

    def pretty_print(self):
        """
        Pretty prints the results
        """
        pp = pprint.PrettyPrinter()
        pp.pprint(self.data)

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
