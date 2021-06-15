"""The greedy algorithm implementation"""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Dict

from src.core.core import server_task_allocation, reset_model
from src.extra.pprint import print_task_values, print_task_allocation
from src.extra.result import Result
from src.greedy.resource_allocation import resource_allocation_functions
from src.greedy.server_selection import server_selection_functions
from src.greedy.task_priority import task_priority_functions

if TYPE_CHECKING:
    from typing import List

    from src.core.server import Server
    from src.core.elastic_task import ElasticTask

    from src.greedy.resource_allocation import ResourceAllocation
    from src.greedy.server_selection import ServerSelection
    from src.greedy.task_priority import TaskPriority


def allocate_tasks(tasks: List[ElasticTask], servers: List[Server], server_selection_policy: ServerSelection,
                   resource_allocation_policy: ResourceAllocation, debug_allocation: bool = False):
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
            server_task_allocation(allocated_server, task, s, w, r)

    if debug_allocation:
        print_task_allocation(tasks)


def greedy_algorithm(tasks: List[ElasticTask], servers: List[Server], task_priority: TaskPriority,
                     server_selection: ServerSelection, resource_allocation: ResourceAllocation,
                     debug_task_values: bool = False, debug_task_allocation: bool = False) -> Result:
    """
    A greedy algorithm to allocate tasks to servers aiming to maximise the total utility,
        the models is stored with the servers and tasks so no return is required

    :param tasks: List of tasks
    :param servers: List of servers
    :param task_priority: The task priority function
    :param server_selection: The selection policy function
    :param resource_allocation: The bid policy function
    :param debug_task_values: The task values debug
    :param debug_task_allocation: The task allocation debug
    """
    start_time = time()

    # Sorted list of task and task priority
    task_values = sorted((task for task in tasks), key=lambda task: task_priority.evaluate(task), reverse=True)
    if debug_task_values:
        print_task_values(sorted(((task, task_priority.evaluate(task)) for task in tasks),
                                 key=lambda jv: jv[1], reverse=True))

    # Run the allocation of the task with the sorted task by value
    allocate_tasks(task_values, servers, server_selection, resource_allocation, debug_allocation=debug_task_allocation)

    # The algorithm name
    algorithm_name = f'Greedy {task_priority.name}, {server_selection.name}, {resource_allocation.name}'
    return Result(algorithm_name, tasks, servers, time() - start_time,
                  **{'task priority': task_priority.name, 'server selection': server_selection.name,
                     'resource allocation': resource_allocation.name})


def greedy_permutations(tasks: List[ElasticTask], servers: List[Server], results: Dict[str, Result], prefix: str = ''):
    for task_priority in task_priority_functions:
        for server_selection in server_selection_functions:
            for resource_allocation in resource_allocation_functions:
                result = greedy_algorithm(tasks, servers, task_priority, server_selection, resource_allocation)
                results[f'{prefix}{result.algorithm}'] = result.store()
                reset_model(tasks, servers)
