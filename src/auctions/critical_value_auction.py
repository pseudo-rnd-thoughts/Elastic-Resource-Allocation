"""A single shot auction in a centralised way"""

from __future__ import annotations

from time import time
from typing import List

from src.core.core import print_task_values
from src.core.task import Task
from src.core.model import reset_model
from src.core.result import Result
from src.core.server import Server
from src.greedy.greedy import allocate_tasks
from src.greedy.resource_allocation_policy import ResourceAllocationPolicy
from src.greedy.server_selection_policy import ServerSelectionPolicy
from src.greedy.value_density import ValueDensity


def calculate_critical_value(critical_task: Task, ranked_tasks: List[Task], servers: List[Server],
                             value_density: ValueDensity, server_selection_policy: ServerSelectionPolicy,
                             resource_allocation_policy: ResourceAllocationPolicy,
                             debug_bound: bool = False) -> float:
    """
    Calculates the critical values of the task

    :param critical_task: The task to find the critical value
    :param ranked_tasks: A sorted list of tasks
    :param servers: A list of servers
    :param value_density: The value density
    :param server_selection_policy: The server selection policy
    :param resource_allocation_policy: The resource allocation policy
    :param debug_bound: Debugs the bound that the task position is being tested at
    :return: The results
    """
    for pos in range(ranked_tasks.index(critical_task) + 1, len(ranked_tasks) - 1):
        reset_model(ranked_tasks, servers)

        ranked_tasks.remove(critical_task)
        ranked_tasks.insert(pos, critical_task)

        # Run the greedy algorithm, allocating the tasks
        allocate_tasks(ranked_tasks, servers, server_selection_policy, resource_allocation_policy)

        if critical_task.running_server:
            if debug_bound:
                print(f'Task allocated to server {critical_task.running_server.name} at position {str(pos)}')
        else:
            density = value_density.evaluate(ranked_tasks[pos - 1])
            return value_density.inverse(critical_task, density)
    return 0


def critical_value_auction(tasks: List[Task], servers: List[Server],
                           value_density: ValueDensity, server_selection_policy: ServerSelectionPolicy,
                           resource_allocation_policy: ResourceAllocationPolicy,
                           debug_task_value: bool = False, debug_greedy_allocation: bool = False,
                           debug_critical_bound: bool = False, debug_critical_value: bool = False) -> Result:
    """
    Critical value auction

    :param tasks: A list of tasks
    :param servers: A list of servers
    :param value_density: The value density function
    :param server_selection_policy: The server selection policy
    :param resource_allocation_policy: The resource allocation policy
    :param debug_task_value: Debug the task value ordering
    :param debug_greedy_allocation: Debug the task allocation
    :param debug_critical_bound: Debug the bound for each task
    :param debug_critical_value: Debug the price for each task
    :return: The results
    """
    start_time = time()

    # Sort the list according to a value density function
    valued_tasks = sorted((task for task in tasks), key=lambda task: value_density.evaluate(task), reverse=True)
    if debug_task_value:
        print_task_values(sorted(((task, value_density.evaluate(task)) for task in tasks),
                                 key=lambda jv: jv[1], reverse=True))

    # Find the allocation of tasks with the list sorted normally
    allocate_tasks(valued_tasks, servers, server_selection_policy, resource_allocation_policy,
                   debug_allocation=debug_greedy_allocation)
    allocation_data = {task: (task.loading_speed, task.compute_speed, task.sending_speed, task.running_server)
                       for task in valued_tasks if task.running_server}

    # Find the task's critical value of the allocated tasks

    task_critical_values = {}
    for task in allocation_data.keys():
        task_critical_values[task] = calculate_critical_value(task, valued_tasks, servers, value_density,
                                                              server_selection_policy, resource_allocation_policy,
                                                              debug_bound=debug_critical_bound)
        if debug_critical_value:
            print(f'Task {task.name} critical value = {task_critical_values[task]:.3f}')

    # Allocate the tasks and set the price to the critical value
    for task, (s, w, r, server) in allocation_data.items():
        price = task_critical_values[task]
        task.allocate(s, w, r, server, price=price)
        server.allocate_task(task)

    return Result(f'Critical Value {value_density.name}, {server_selection_policy.name}, '
                  f'{resource_allocation_policy.name}', tasks, servers, time() - start_time, show_money=True,
                  value_density=value_density.name, server_selection_policy=server_selection_policy.name,
                  resource_allocation_policy=resource_allocation_policy.name)
