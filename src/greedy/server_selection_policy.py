"""Allocation policy functions"""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import exp
from random import choice
from typing import List, Optional

from src.core.job import Job
from src.core.server import Server
from src.greedy.resource_allocation_policy import ResourceAllocationPolicy, policies as resource_allocation_policies


class ServerSelectionPolicy(ABC):
    """Server Selection Policy"""

    def __init__(self, name: str, maximise: bool = False):
        self.name = name
        self.maximise = maximise

    def select(self, job: Job, servers: List[Server]) -> Optional[Server]:
        """
        Select the server that maximises the value function
        :param job: The job
        :param servers: The list of servers
        :return: The selected server
        """
        if self.maximise:
            return max(((server, self.value(job, server)) for server in servers if server.can_run(job)),
                       key=lambda sv: sv[1], default=[None])[0]
        else:
            return min(((server, self.value(job, server)) for server in servers if server.can_run(job)),
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

    def __init__(self, maximise: bool = False):
        super().__init__("Sum", maximise)

    def value(self, job: Job, server: Server) -> float:
        """Server Selection Value"""
        return server.available_storage + server.available_computation + server.available_bandwidth


class ProductResources(ServerSelectionPolicy):
    """The product of a server's available resources"""

    def __init__(self, maximise: bool = False):
        super().__init__("Product", maximise)

    def value(self, job: Job, server: Server) -> float:
        """Server Selection Value"""
        return server.available_storage * server.available_computation * server.available_bandwidth


class SumExpResource(ServerSelectionPolicy):
    """The sum of a server's available resources"""

    def __init__(self, maximise: bool = False):
        super().__init__("Exponential Sum", maximise)

    def value(self, job: Job, server: Server) -> float:
        """Server Selection Value"""
        return exp(server.available_storage) + exp(server.available_computation) + exp(server.available_bandwidth)


class Random(ServerSelectionPolicy):
    """A random number"""

    def __init__(self, maximise: bool = False):
        super().__init__("Random", maximise)

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


class JobSumResources(ServerSelectionPolicy):
    """Job Sum resources usage"""

    def __init__(self, resource_allocation_policy: ResourceAllocationPolicy, maximise: bool = False):
        super().__init__("Job Sum of {}".format(resource_allocation_policy.name), maximise)

        self.resource_allocation_policy = resource_allocation_policy

    def value(self, job: Job, server: Server) -> float:
        """Value function"""
        loading, compute, sending = self.resource_allocation_policy.allocate(job, server)
        return job.required_storage / server.available_storage + \
               compute / server.available_computation + \
               (loading + sending) / server.available_bandwidth


policies = [
    SumResources(),
    ProductResources(),
    SumExpResource(),
    Random()
]

all_policies = [
    policy(maximise)
    for maximise in [True, False]
    for policy in [SumResources, ProductResources, SumExpResource, Random]
]
all_policies += [
    JobSumResources(policy, maximise)
    for maximise in [True, False]
    for policy in resource_allocation_policies
]

max_name_length = max(len(policy.name) for policy in policies)
