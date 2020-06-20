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
from typing import TYPE_CHECKING

from core.core import server_task_allocation, reset_model, debug
from extra.result import Result
from greedy.greedy import allocate_tasks

if TYPE_CHECKING:
    from typing import List, Dict, Tuple

    from core.server import Server
    from core.task import Task

    from greedy.resource_allocation_policy import ResourceAllocationPolicy
    from greedy.server_selection_policy import ServerSelectionPolicy
    from greedy.value_density import ValueDensity


def critical_value_auction(tasks: List[Task], servers: List[Server], value_density: ValueDensity,
                           server_selection_policy: ServerSelectionPolicy,
                           resource_allocation_policy: ResourceAllocationPolicy,
                           debug_initial_allocation: bool = False, debug_critical_value: bool = False) -> Result:
    """
    Run the Critical value auction

    :param tasks: List of tasks
    :param servers: List of servers
    :param value_density: Value density function
    :param server_selection_policy: Server selection function
    :param resource_allocation_policy: Resource allocation function
    :param debug_initial_allocation: If to debug the initial allocation
    :param debug_critical_value: If to debug the critical value
    :return: The results from the auction
    """
    start_time = time()

    valued_tasks: Dict[Task, float] = {task: value_density.evaluate(task) for task in tasks}
    ranked_tasks: List[Task] = sorted(valued_tasks, key=lambda j: valued_tasks[j], reverse=True)

    # Runs the greedy algorithm
    allocate_tasks(ranked_tasks, servers, server_selection_policy, resource_allocation_policy)
    allocation_data: Dict[Task, Tuple[int, int, int, Server]] = {
        task: (task.loading_speed, task.compute_speed, task.sending_speed, task.running_server)
        for task in ranked_tasks if task.running_server
    }

    if debug_initial_allocation:
        max_name_len = max(len(task.name) for task in tasks)
        print(f"{'Task':<{max_name_len}} | s | w | r | server")
        for task, (s, w, r, server) in allocation_data.items():
            print(f'{task:<{max_name_len}}|{s:3f}|{w:3f}|{r:3f}|{server.name}')

    reset_model(tasks, servers)

    # Loop through each task allocated and find the critical value for the task
    for critical_task in allocation_data.keys():
        # Remove the task from the ranked tasks and save the original position
        critical_pos = ranked_tasks.index(critical_task)
        ranked_tasks.remove(critical_task)

        # Loop though the tasks in order checking if the task can be allocated at any point
        for task_pos, task in enumerate(ranked_tasks):
            # If any of the servers can allocate the critical task then allocate the current task to a server
            if any(server.can_run(critical_task) for server in servers):
                server = server_selection_policy.select(task, servers)
                if server:  # There may not be a server that can allocate the task
                    s, w, r = resource_allocation_policy.allocate(task, server)
                    server_task_allocation(server, task, s, w, r)
            else:
                # If critical task isn't able to be allocated therefore the last task's density is found
                #   and the inverse of the value density is calculated with the last task's density.
                #   If the task can always run then the price is zero, the default price so no changes need to be made
                critical_task_density = valued_tasks[ranked_tasks[task_pos - 1]]
                critical_task.price = round(value_density.inverse(critical_task, critical_task_density), 3)
                break

        debug(f'{critical_task.name} Task critical value: {critical_task.price:.3f}', debug_critical_value)

        # Read the task back into the ranked task in its original position and reset the model but not forgetting the
        #   new critical task's price
        ranked_tasks.insert(critical_pos, critical_task)
        reset_model(tasks, servers, forgot_price=False)

    # Allocate the tasks and set the price to the critical value
    for task, (s, w, r, server) in allocation_data.items():
        server_task_allocation(server, task, s, w, r)

    return Result(f'Critical Value Auction', tasks, servers, time() - start_time, is_auction=True,
                  value_density=value_density.name, server_selection_policy=server_selection_policy.name,
                  resource_allocation_policy=resource_allocation_policy.name)
