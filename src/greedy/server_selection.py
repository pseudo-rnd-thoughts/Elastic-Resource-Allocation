"""Allocation policy functions"""

from __future__ import annotations

from abc import ABC, abstractmethod
from random import choice, gauss
from typing import TYPE_CHECKING

from src.greedy.resource_allocation import resource_allocation_functions

if TYPE_CHECKING:
    from typing import List, Optional

    from src.core.server import Server
    from src.core.elastic_task import ElasticTask
    from src.greedy.resource_allocation import ResourceAllocation


class ServerSelection(ABC):
    """Server Selection function"""

    def __init__(self, name: str, maximise: bool = False, long_name: bool = False):
        if long_name:
            self.name = f"{'maximise' if maximise else 'minimise'} {name}"
        else:
            self.name = name
        self.maximise = maximise

    def select(self, task: ElasticTask, servers: List[Server]) -> Optional[Server]:
        """
        Select the server that maximises the value function

        :param task: The task
        :param servers: The list of servers
        :return: The selected server
        """
        if self.maximise:
            return max((server for server in servers if server.can_run(task)),
                       key=lambda server: self.value(task, server), default=None)
        else:
            return min((server for server in servers if server.can_run(task)),
                       key=lambda server: self.value(task, server), default=None)

    @abstractmethod
    def value(self, task: ElasticTask, server: Server) -> float:
        """
        The value of the server and task combination

        :param task: The task
        :param server: The server
        :return: The value of the combination
        """
        pass


class SumResources(ServerSelection):
    """The sum of a server's available resources"""

    def __init__(self, maximise: bool = False):
        ServerSelection.__init__(self, 'Sum', maximise)

    def value(self, task: ElasticTask, server: Server) -> float:
        """Server Selection Value"""
        return server.available_storage + server.available_computation + server.available_bandwidth


class ProductResources(ServerSelection):
    """The product of a server's available resources"""

    def __init__(self, maximise: bool = False):
        ServerSelection.__init__(self, 'Product', maximise)

    def value(self, task: ElasticTask, server: Server) -> float:
        """Server Selection Value"""
        return server.available_storage * server.available_computation * server.available_bandwidth


class SumExpResource(ServerSelection):
    """The sum of a server's available resources"""

    def __init__(self, maximise: bool = False):
        ServerSelection.__init__(self, 'Exponential Sum', maximise)

    def value(self, task: ElasticTask, server: Server) -> float:
        """Server Selection Value"""
        return server.available_storage ** 3 + server.available_computation ** 3 + server.available_bandwidth ** 3


class Random(ServerSelection):
    """A random number"""

    def __init__(self, maximise: bool = False):
        ServerSelection.__init__(self, 'Random', maximise)

    def select(self, task: ElasticTask, servers: List[Server]) -> Optional[Server]:
        """Selects the server"""
        runnable_servers = [server for server in servers if server.can_run(task)]
        if runnable_servers:
            return choice(runnable_servers)
        else:
            return None

    def value(self, task: ElasticTask, server: Server) -> float:
        """Value function"""
        raise NotImplementedError('Value function not implemented')


class TaskSumResources(ServerSelection):
    """Job Sum resources usage"""

    def __init__(self, resource_allocation_policy: ResourceAllocation, maximise: bool = False):
        ServerSelection.__init__(self, f'Job Sum of {resource_allocation_policy.name}', maximise)

        self.resource_allocation_policy = resource_allocation_policy

    def value(self, task: ElasticTask, server: Server) -> float:
        """Value function"""
        loading, compute, sending = self.resource_allocation_policy.allocate(task, server)
        return task.required_storage / server.available_storage + \
            compute / server.available_computation + \
            (loading + sending) / server.available_bandwidth


class EvolutionStrategy(ServerSelection):
    """Covariance matrix adaption evolution strategy"""

    def __init__(self, name: int, avail_storage_var: Optional[float] = None, avail_comp_var: Optional[float] = None,
                 avail_bandwidth_var: Optional[float] = None, maximise: bool = True):
        ServerSelection.__init__(self, f'CMS-ES {name}', maximise)

        self.avail_storage_var = avail_storage_var if avail_storage_var else gauss(0, 1)
        self.avail_comp_var = avail_comp_var if avail_comp_var else gauss(0, 1)
        self.avail_bandwidth_var = avail_bandwidth_var if avail_bandwidth_var else gauss(0, 1)

    def value(self, task: ElasticTask, server: Server) -> float:
        """Value function"""
        return self.avail_storage_var * server.available_storage + \
            self.avail_comp_var * server.available_computation + \
            self.avail_bandwidth_var * server.available_bandwidth


server_selection_functions = [
    SumResources(),
    ProductResources()
]

all_server_selection_functions = [
    func(maximise)
    for maximise in [True, False]
    for func in [SumResources, ProductResources, SumExpResource, Random]
]
all_server_selection_functions += [
    TaskSumResources(func, maximise)
    for maximise in [True, False]
    for func in resource_allocation_functions
]
