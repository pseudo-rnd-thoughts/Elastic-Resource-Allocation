"""Implementation of an VCG auctions"""

from __future__ import annotations

from time import time
from typing import List, Dict, Tuple, Optional

from src.core.core import list_copy_remove
from src.core.task import Task
from src.core.model import reset_model
from src.core.result import Result
from src.core.server import Server
from src.optimal.optimal import optimal_algorithm


def vcg_auction(tasks: List[Task], servers: List[Server], time_limit: int,
                debug_running: bool = False, debug_results: bool = False) -> Optional[Result]:
    """
    Implementation of a VCG auctions

    :param tasks: A list of tasks
    :param servers: A list of servers
    :param time_limit: The time to run the optimal for
    :param debug_running: Debug what is being calculated
    :param debug_results: Debug the results for each task and server
    """
    start_time = time()

    # Price information
    task_prices: Dict[Task, float] = {}

    # Find the optimal solution
    if debug_running:
        print('Finding optimal')
    optimal_solution = optimal_algorithm(tasks, servers, time_limit=time_limit)
    if optimal_solution is None:
        return None
    elif debug_results:
        print(f'Optimal total utility: {optimal_solution.sum_value}')

    # Save the task and server information from the optimal solution
    allocated_tasks = [task for task in tasks if task.running_server]
    task_info: Dict[Task, Tuple[int, int, int, Server]] = {
        task: (task.loading_speed, task.compute_speed, task.sending_speed, task.running_server) for task in tasks
    }

    if debug_running:
        print(f"Allocated tasks: {', '.join([task.name for task in allocated_tasks])}")

    # For each allocated task, find the sum of values if the task doesnt exist
    for task in allocated_tasks:
        # Reset the model and remove the task from the task list
        reset_model(tasks, servers)
        tasks_prime = list_copy_remove(tasks, task)

        # Find the optimal solution where the task doesnt exist
        if debug_running:
            print(f'Solving for without task {task.name}')
        optimal_prime = optimal_algorithm(tasks_prime, servers, time_limit=time_limit)
        if optimal_prime is None:
            return None
        else:
            task_prices[task] = optimal_solution.sum_value - optimal_prime.sum_value
            if debug_results:
                print(f'Task {task.name}: £{task_prices[task]:.1f}, Value: {task.value} ')

    # Reset the model and allocates all of the their info from the original optimal solution
    reset_model(tasks, servers)
    for task in allocated_tasks:
        s, w, r, server = task_info[task]
        task.allocate(s, w, r, server, price=task_prices[task])
        server.allocate_task(task)

    return Result('vcg', tasks, servers, time() - start_time, individual_compute_time=time_limit, show_money=True)
