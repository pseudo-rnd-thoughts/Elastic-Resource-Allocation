"""
Fixed Greedy algorithm
"""

from typing import List, Tuple

from core.fixed_task import FixedTask
from core.server import Server
from core.task import Task
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import ResourceAllocationPolicy
from greedy.server_selection_policy import ServerSelectionPolicy
from greedy.value_density import ValueDensity


def fixed_greedy_algorithm(tasks: List[FixedTask], servers: List[Server],
                           value_density: ValueDensity, server_selection: ServerSelectionPolicy):
    """
    Runs the greedy algorithm using a fixed resource allocation policy

    :param tasks: List of tasks
    :param servers: List of servers
    :param value_density: Value density function
    :param server_selection: Server selection policy
    :return: Results
    """

    result = greedy_algorithm(tasks, servers, value_density, server_selection, FixedResourceAllocationPolicy())
    # Update the algorithm name
    result.data['algorithm'].replace('Greedy', 'Fixed Greedy').replace(', Fixed Task Speeds', '')
    return result


class FixedResourceAllocationPolicy(ResourceAllocationPolicy):
    """Fixed Resource Allocation Policy"""

    def __init__(self):
        ResourceAllocationPolicy.__init__(self, 'Fixed Task Speeds')

    def allocate(self, task: Task, server: Server) -> Tuple[int, int, int]:
        """
        Allocates a task's speeds that must be a fixed task

        :param task: A fixed task
        :param server: The server
        :return: The fixed task's speeds
        """
        assert type(task) is FixedTask

        return task.loading_speed, task.compute_speed, task.sending_speed

    def resource_evaluator(self, task: Task, server: Server, loading_speed: int, compute_speed: int,
                           sending_speed: int) -> float:
        """Resource evaluator"""

        raise NotImplementedError()
