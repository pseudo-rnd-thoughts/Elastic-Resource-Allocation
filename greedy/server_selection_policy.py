"""Allocation policy functions"""

from __future__ import annotations
from abc import ABC, abstractmethod
from math import exp
from random import choice
from typing import List, Optional

from core.job import Job
from core.server import Server


class ServerSelectionPolicy(ABC):
    """Server Selection Policy"""

    def __init__(self, name):
        self.name = name

    def select(self, job: Job, servers: List[Server]) -> Optional[Server]:
        """
        Select the server that maximises the value function
        :param job: The job
        :param servers: The list of servers
        :return: The selected server
        """
        return max(((server, self.value(job, server)) for server in servers if server.can_run(job)),
                   key=lambda sv: sv[1], default=[None])[0]

    @abstractmethod
    def value(self, job: Job, server: Server) -> float:
        """
        The value of the server and job combination
        :param job: The job
        :param server: The server
        :return: The value of the combination
        """
        pass


class SumResources(ServerSelectionPolicy):
    """The sum of a server's available resources"""

    def __init__(self):
        super().__init__("Resources Sum")

    def value(self, job: Job, server: Server) -> float:
        """Server Selection Value"""
        return server.available_storage + server.available_computation + server.available_bandwidth


class ProductResources(ServerSelectionPolicy):
    """The product of a server's available resources"""

    def __init__(self):
        super().__init__("Resources Product")

    def value(self, job: Job, server: Server) -> float:
        """Server Selection Value"""
        return server.available_storage * server.available_computation * server.available_bandwidth


class SumExpResource(ServerSelectionPolicy):
    """The sum of a server's available resources"""

    def __init__(self):
        super().__init__("Resources Exponential Sum")

    def value(self, job: Job, server: Server) -> float:
        """Server Selection Value"""
        return exp(server.available_storage) + exp(server.available_computation) + exp(server.available_bandwidth)


class Random(ServerSelectionPolicy):
    """A random number"""

    def __init__(self):
        super().__init__("Random")

    def select(self, job: Job, servers: List[Server]) -> Optional[Server]:
        """Selects the server"""
        runnable_servers = [server for server in servers if server.can_run(job)]
        if runnable_servers:
            return choice(runnable_servers)
        else:
            return None

    def value(self, job: Job, server: Server) -> float:
        """Value function"""
        raise NotImplementedError("Value function not implemented")


policies = (
    SumResources(),
    ProductResources(),
    SumExpResource(),
    Random()
)
