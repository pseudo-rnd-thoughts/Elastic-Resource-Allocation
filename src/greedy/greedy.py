"""The greedy algorithm implementation"""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING

from extra.pprint import print_task_values, print_task_allocation
from core.result import Result

if TYPE_CHECKING:
    from typing import List

    from core.server import Server
    from core.task import Task

    from greedy.resource_allocation_policy import ResourceAllocationPolicy
    from greedy.server_selection_policy import ServerSelectionPolicy
    from greedy.value_density import ValueDensity


def greedy_algorithm(tasks: List[Task], servers: List[Server], value_density: ValueDensity,
                     server_selection_policy: ServerSelectionPolicy,
                     resource_allocation_policy: ResourceAllocationPolicy, debug_task_values: bool = False,
                     debug_task_allocation: bool = False) -> Result:
    """
    A greedy algorithm to allocate tasks to servers aiming to maximise the total utility,
        the models is stored with the servers and tasks so no return is required

    :param tasks: List of tasks
    :param servers: List of servers
    :param value_density: The value density function
    :param server_selection_policy: The selection policy function
    :param resource_allocation_policy: The bid policy function
    :param debug_task_values: The task values debug
    :param debug_task_allocation: The task allocation debug
    """
    start_time = time()

    # Sorted list of task and value density
    task_values = sorted((task for task in tasks), key=lambda task: value_density.evaluate(task), reverse=True)
    if debug_task_values:
        print_task_values(sorted(((task, value_density.evaluate(task)) for task in tasks),
                                 key=lambda jv: jv[1], reverse=True))

    # Run the allocation of the task with the sorted task by value
    allocate_tasks(task_values, servers, server_selection_policy, resource_allocation_policy,
                   debug_allocation=debug_task_allocation)

    # The algorithm name
    algorithm_name = f'Greedy {value_density.name}, {server_selection_policy.name}, {resource_allocation_policy.name}'
    return Result(algorithm_name, tasks, servers, time() - start_time,
                  value_density=value_density.name, server_selection_policy=server_selection_policy.name,
                  resource_allocation_policy=resource_allocation_policy.name)


def allocate_tasks(tasks: List[Task], servers: List[Server], server_selection_policy: ServerSelectionPolicy,
                   resource_allocation_policy: ResourceAllocationPolicy, debug_allocation: bool = False):
    """
    Allocate the tasks to the servers based on the server selection policy and resource allocation policies

    :param tasks: The list of tasks
    :param servers: The list of servers
    :param server_selection_policy: The server selection policy
    :param resource_allocation_policy: The resource allocation policy
    :param debug_allocation: The task allocation debug
    """

    # Loop through all of the task in order of values
    for task in tasks:
        # Allocate the server using the allocation policy function
        allocated_server = server_selection_policy.select(task, servers)

        # If an optimal server is found then calculate the bid allocation function
        if allocated_server:
            s, w, r = resource_allocation_policy.allocate(task, allocated_server)
            task.allocate(s, w, r, allocated_server)
            allocated_server.allocate_task(task)

    if debug_allocation:
        print_task_allocation(tasks)
