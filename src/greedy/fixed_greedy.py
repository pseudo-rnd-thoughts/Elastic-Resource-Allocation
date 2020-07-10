"""
Fixed Greedy algorithm
"""

from typing import List

from core.fixed_task import FixedTask
from core.server import Server
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import FixedResourceAllocationPolicy
from greedy.server_selection_policy import ServerSelectionPolicy
from greedy.value_density import ValueDensity


def fixed_greedy(tasks: List[FixedTask], servers: List[Server],
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
