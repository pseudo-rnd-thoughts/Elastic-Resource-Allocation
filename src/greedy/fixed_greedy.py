"""
Fixed Greedy algorithm
"""

from typing import List

from core.server import Server
from core.task import Task
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import FixedResourceAllocationPolicy
from greedy.server_selection_policy import ServerSelectionPolicy
from greedy.value_density import ValueDensity


def fixed_greedy(tasks: List[Task], servers: List[Server],
                 value_density: ValueDensity, server_selection: ServerSelectionPolicy):

    result = greedy_algorithm(tasks, servers, value_density, server_selection, FixedResourceAllocationPolicy())
    result.data['algorithm'].replace('Greedy', 'Fixed Greedy').replace(', Fixed Task Speeds', '')
    return result
