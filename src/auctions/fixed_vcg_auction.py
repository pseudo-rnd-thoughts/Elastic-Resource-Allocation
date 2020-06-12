"""Combinatorial Double Auction"""

from __future__ import annotations

from time import time
from typing import List, Dict, Optional

from src.branch_bound.branch_bound import branch_bound_algorithm
from src.branch_bound.feasibility_allocations import fixed_feasible_allocation
from src.core.core import allocate, list_copy_remove
from src.core.fixed_task import FixedTask
from src.core.model import reset_model
from src.core.result import Result
from src.core.server import Server
from src.core.task import Task


def fixed_vcg_auction(tasks: List[FixedTask], servers: List[Server],
                      debug_running: bool = False, debug_results: bool = False) -> Optional[Result]:
    """
    Combinatorial Double auction solved through VCG auction algorithm
    :param tasks: a list of tasks
    :param servers: a list of servers
    :param debug_running: debug the running
    :param debug_results: debug the results
    :return: the results
    """
    start_time = time()

    # Price information
    task_prices: Dict[Task, float] = {}

    # Find the optimal solution
    if debug_running:
        print("Finding optimal")
    optimal_solution = branch_bound_algorithm(tasks, servers, fixed_feasible_allocation)
    if optimal_solution is None:
        return None
    elif debug_results:
        print("Optimal total utility: {}".format(optimal_solution))

    # Save the task and server information from the optimal solution
    allocated_tasks = [task for task in tasks if task.running_server]
    task_allocation: Dict[Task, Server] = {task: task.running_server for task in tasks}

    if debug_running:
        print("Allocated tasks: {}".format(", ".join([task.name for task in allocated_tasks])))

    # For each allocated task, find the sum of values if the task doesnt exist
    for task in allocated_tasks:
        # Reset the model and remove the task from the task list
        reset_model(tasks, servers)
        tasks_prime = list_copy_remove(tasks, task)

        # Find the optimal solution where the task doesnt exist
        if debug_running:
            print("Solving for without {} task".format(task.name))
        optimal_prime = branch_bound_algorithm(tasks_prime, servers, fixed_feasible_allocation)
        if optimal_prime is None:
            return None
        else:
            task_prices[task] = optimal_solution.sum_value - optimal_prime.sum_value
            if debug_results:
                print("Job {}: £{:.1f}, Value: {} ".format(task.name, task_prices[task], task.value))

    # Resets all of the tasks and servers and allocates all of their info from the original optimal solution
    reset_model(tasks, servers)
    for task in allocated_tasks:
        allocate(task, -1, -1, -1, task_allocation[task], task_prices[task])

    return Result('vcg', tasks, servers, time() - start_time, show_money=True)
