"""
Greedy algorithm using a matrix of task and server resource allocation values
"""

from __future__ import annotations

from time import time
from typing import List, Tuple

from src.core.core import allocate
from src.core.task import Task
from src.core.result import Result
from src.core.server import Server
from src.greedy_matrix.allocation_value_policy import AllocationValuePolicy


def allocate_resources(task: Task, server: Server, value: AllocationValuePolicy) -> Tuple[float, int, int, int]:
    """
    Calculates the value of a server task allocation with the resources allocated

    :param task: A task
    :param server: A server
    :param value: The value policy
    :return: The tuple of values and resource allocations
    """
    return max(((value.evaluate(task, server, s, w, r), s, w, r)
                for s in range(1, server.available_bandwidth + 1)
                for w in range(1, server.available_computation + 1)
                for r in range(1, server.available_bandwidth - s + 1)
                if task.required_storage * w * r + s * task.required_computation * r +
                s * w * task.required_results_data <= task.deadline * s * w * r), key=lambda x: x[0])


def matrix_greedy(tasks: List[Task], servers: List[Server], allocation_value_policy: AllocationValuePolicy,
                  debug_allocation: bool = False, debug_pop: bool = False) -> Result:
    """
    A greedy algorithm that uses the idea of a matrix

    :param tasks: A list of tasks
    :param servers: A list of servers
    :param allocation_value_policy: The value matrix policy
    :param debug_allocation: Debugs the allocation
    :param debug_pop: Debugs the values that are popped
    :return: The results
    """
    start_time = time()

    # Generate the full allocation value matrix
    allocation_value_matrix = {(task, server): allocate_resources(task, server, allocation_value_policy)
                               for task in tasks for server in servers if server.can_run(task)}
    unallocated_tasks = tasks.copy()

    # Loop over the allocation matrix till there are no values left
    while len(allocation_value_matrix):
        (allocated_task, allocated_server), (v, s, w, r) = max(allocation_value_matrix.items(), key=lambda x: x[1][0])
        allocate(allocated_task, s, w, r, allocated_server)
        if debug_allocation:
            print(f'Task {allocated_task.name} on Server {allocated_server.name} '
                  f'with value {v:.3f}, loading {s} compute {w} sending {r}')

        # Remove the task from the allocation matrix
        for server in servers:
            if (allocated_task, server) in allocation_value_matrix:
                if debug_pop:
                    print(f'Pop task {allocated_task.name} and server {server.name}')
                allocation_value_matrix.pop((allocated_task, server))

        # Remove the task from the unallocated tasks and check if the allocated server can now not run any of the tasks
        unallocated_tasks.remove(allocated_task)
        for task in unallocated_tasks:
            # Update the allocation when the server is updated
            if allocated_server.can_run(task):
                allocation_value_matrix[(task, allocated_server)] = allocate_resources(task, allocated_server,
                                                                                       allocation_value_policy)
            # If task cant be run then remove the task
            elif (task, allocated_server) in allocation_value_matrix:
                if debug_pop:
                    print(f'Pop task {task.name} and server {allocated_server.name}')
                allocation_value_matrix.pop((task, allocated_server))

    return Result(f'Matrix Greedy {allocation_value_policy.name}', tasks, servers, solve_time=time() - start_time)
