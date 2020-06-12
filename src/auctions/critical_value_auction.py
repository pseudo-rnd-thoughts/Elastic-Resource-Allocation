"""
Implementation of a critical value auction using the greedy algorithm in order to determine allocation

Algorithm steps
1. Run greedy algorithm with task value's
2. For all of the task's allocated by the greedy algorithm
    1. Determine the minimum point in the task value density list where the task will still be allocated
    2. Using the inverse value density function and the elimination task's value to calculate the task's critical value
"""

from __future__ import annotations

from time import time
from typing import List, Dict

from src.core.core import print_task_values, allocate
from src.core.task import Task
from src.core.model import reset_model
from src.core.result import Result
from src.core.server import Server
from src.greedy.greedy import allocate_tasks
from src.greedy.resource_allocation_policy import ResourceAllocationPolicy
from src.greedy.server_selection_policy import ServerSelectionPolicy
from src.greedy.value_density import ValueDensity


def critical_value(critical_task: Task, ordered_tasks: List[Task], servers: List[Server], value_density: ValueDensity,
                   server_selection_policy: ServerSelectionPolicy,
                   resource_allocation_policy: ResourceAllocationPolicy) -> float:
    """
    Calculates the critical values of a task

    :param critical_task: Task to find the critical value of
    :param ordered_tasks: List of task's sorted by value density (including the critical task)
    :param servers: A list of servers for task's to be allocated to
    :param value_density: The value density function
    :param server_selection_policy: The server selection policy
    :param resource_allocation_policy: The resource allocation policy
    :return: the critical value of the task
    """
    # To optimise, the tasks in order are allocated to a server based on the server selection and resource allocation
    #   policies till the critical task can't be allocated to any of the servers
    critical_task_reached = False
    for pos, task in enumerate(ordered_tasks):
        # If the task is the critical task, ignore it as we don't want to allocate it
        if task is critical_task:
            critical_task_reached = True
            continue
        else:
            # Else allocate the current task to any of the servers
            server = server_selection_policy.select(task, servers)
            s, w, r = resource_allocation_policy.allocate(task, server)
            allocate(task, s, w, r, server)

            # If the critical task has been reached and no server can run the critical value then
            #   determine the critical density and critical value
            if critical_task_reached and not any(server.can_run(critical_task) for server in servers):
                density = value_density.evaluate(task)
                return value_density.inverse(critical_task, density)

    # If the task can still be allocated after all other task's have been allocated then the task has a critical value
    #   of zero as the task doesn't stop any other task from running
    return 0


def critical_value_auction(tasks: List[Task], servers: List[Server],
                           value_density: ValueDensity, server_selection_policy: ServerSelectionPolicy,
                           resource_allocation_policy: ResourceAllocationPolicy) -> Result:
    """
    Runs the critical value auction

    :param tasks: A list of tasks
    :param servers: A list of servers
    :param value_density: The value density function
    :param server_selection_policy: The server selection policy
    :param resource_allocation_policy: The resource allocation policy
    :return: The results of the critical value auction
    """
    start_time = time()
    # 1. Runs the greedy algorithm normally by sorting the tasks by value density then allocating tasks to servers
    ordered_tasks = sorted((task for task in tasks), key=lambda task: value_density.evaluate(task), reverse=True)
    allocate_tasks(ordered_tasks, servers, server_selection_policy, resource_allocation_policy)

    # Store the resource allocation of all task's allocated to a server
    resource_allocation = {task: (task.loading_speed, task.compute_speed, task.sending_speed, task.running_server)
                           for task in ordered_tasks if task.running_server}

    # Find the critical value for each task of the allocated tasks
    critical_values: Dict[Task, float] = {}
    for task in resource_allocation.keys():
        reset_model(tasks, servers)
        critical_values[task] = critical_value(task, ordered_tasks, servers, value_density,
                                               server_selection_policy, resource_allocation_policy)

    # Allocate the tasks and set the price to the critical value
    reset_model(tasks, servers)
    for task, (s, w, r, server) in resource_allocation.items():
        allocate(task, s, w, r, server, price=critical_values[task])

    return Result(f'Critical Value {value_density.name}, {server_selection_policy.name}, {resource_allocation_policy.name}',
                  tasks, servers, time() - start_time, show_money=True, value_density=value_density.name,
                  server_selection_policy=server_selection_policy.name,
                  resource_allocation_policy=resource_allocation_policy.name)
