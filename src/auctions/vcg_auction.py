"""
Implementation of an VCG auctions

Todo add update for choice optimal solver
Todo add fixed_vcg auction
"""

from __future__ import annotations

import functools
from time import time
from typing import TYPE_CHECKING

from core.core import list_copy_remove, reset_model, server_task_allocation, debug
from core.result import Result
from optimal.fixed_optimal import fixed_optimal_algorithm
from optimal.optimal import optimal_algorithm

if TYPE_CHECKING:
    from typing import List, Dict, Tuple, Optional

    from core.server import Server
    from core.task import Task
    from core.fixed_task import FixedTask


def vcg_solver(tasks: List[Task], servers: List[Server], solver, debug_running: bool = False) -> float:
    """
    VCG auction solver

    :param tasks: List of tasks
    :param servers: List of servers
    :param solver: Solver to find solution
    :param debug_running: If to debug the running algorithm
    :return: Total solve time
    """
    start_time = time()

    # Price information
    task_prices: Dict[Task, float] = {}

    # Find the optimal solution
    debug('Running optimal solution', debug_running)
    optimal_results = solver(tasks, servers)
    if optimal_results is None:
        return 0
    optimal_social_welfare = optimal_results.social_welfare
    debug(f'Optimal social welfare: {optimal_social_welfare}', debug_running)

    # Save the task and server information from the optimal solution
    allocated_tasks = [task for task in tasks if task.running_server]
    task_allocation: Dict[Task, Tuple[int, int, int, Server]] = {
        task: (task.loading_speed, task.compute_speed, task.sending_speed, task.running_server)
        for task in allocated_tasks
    }

    debug(f"Allocated tasks: {', '.join([task.name for task in allocated_tasks])}", debug_running)

    # For each allocated task, find the sum of values if the task doesnt exist
    for task in allocated_tasks:
        # Reset the model and remove the task from the task list
        reset_model(tasks, servers)
        tasks_prime = list_copy_remove(tasks, task)

        # Find the optimal solution where the task doesnt exist
        debug(f'Solving for without task {task.name}', debug_running)
        prime_results = solver(tasks_prime, servers)
        if prime_results is None:
            return 0
        else:
            task_prices[task] = optimal_social_welfare - prime_results.social_welfare
            debug(f'{task.name} Task: £{task_prices[task]:.1f}, Value: {task.value} ', debug_running)

    # Reset the model and allocates all of the their info from the original optimal solution
    reset_model(tasks, servers)
    for task, (s, w, r, server) in task_allocation.items():
        server_task_allocation(server, task, s, w, r, price=task_prices[task])

    return time() - start_time


def vcg_auction(tasks: List[Task], servers: List[Server], time_limit: int = 5,
                debug_results: bool = False) -> Optional[Result]:
    """
    VCG auction algorithm

    :param tasks: List of tasks
    :param servers: List of servers
    :param time_limit: The time limit of the optimal solver
    :param debug_results: If to debug results
    :return: The results of the VCG auction
    """
    optimal_solver = functools.partial(optimal_algorithm, time_limit=time_limit)

    solve_time = vcg_solver(tasks, servers, optimal_solver, debug_results)
    if 0 < solve_time:
        return Result('VCG', tasks, servers, solve_time, is_auction=True)


def fixed_vcg_auction(fixed_tasks: List[FixedTask], servers: List[Server], time_limit: int = 5,
                      debug_results: bool = False) -> Optional[Result]:
    """
    Fixed VCG auction algorithm

    :param fixed_tasks: List of the fixed tasks
    :param servers: List of servers
    :param time_limit: The limit of the fixed optimal solver
    :param debug_results: If to debug results
    :return: The results of the fixed VCG auction
    """
    fixed_solver = functools.partial(fixed_optimal_algorithm, time_limit=time_limit)

    solve_time = vcg_solver(fixed_tasks, servers, fixed_solver, debug_results)
    if 0 < solve_time:
        return Result('Fixed VCG', fixed_tasks, servers, solve_time, is_auction=True)
