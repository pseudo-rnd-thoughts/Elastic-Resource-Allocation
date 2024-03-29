"""
Implementation of an VCG auctions
"""

from __future__ import annotations

import functools
import sys
from typing import TYPE_CHECKING, TypeVar, Callable

from docplex.cp.solution import CpoSolveResult

from src.core.core import reset_model, server_task_allocation, debug
from src.extra.result import Result
from src.optimal.non_elastic_optimal import non_elastic_optimal_solver
from src.optimal.elastic_optimal import elastic_optimal_solver

if TYPE_CHECKING:
    from typing import List, Dict, Tuple, Optional

    from src.core.server import Server
    from src.core.elastic_task import ElasticTask
    from src.core.non_elastic_task import NonElasticTask

    T = TypeVar('T')


def list_copy_remove(lists: List[T], item: T) -> List[T]:
    """
    Copy the list and remove an item

    :param lists: The list
    :param item: The item to remove
    :return: The copied list without the item
    """

    list_copy = lists.copy()
    list_copy.remove(item)

    return list_copy


def vcg_solver(tasks: List[ElasticTask], servers: List[Server], solver: Callable,
               debug_running: bool = False) -> Optional[CpoSolveResult]:
    """
    VCG auction solver

    :param tasks: List of tasks
    :param servers: List of servers
    :param solver: Solver to find solution
    :param debug_running: If to debug the running algorithm
    :return: Total solve time
    """
    # Price information
    task_prices: Dict[ElasticTask, float] = {}

    # Find the optimal solution
    debug('Running optimal solution', debug_running)
    optimal_results = solver(tasks, servers)
    if optimal_results is None:
        print(f'Optimal solver failed')
        return None
    optimal_social_welfare = sum(task.value for task in tasks if task.running_server)
    debug(f'Optimal social welfare: {optimal_social_welfare}', debug_running)

    # Save the task and server information from the optimal solution
    allocated_tasks = [task for task in tasks if task.running_server]
    task_allocation: Dict[ElasticTask, Tuple[int, int, int, Server]] = {
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
            print(f'Failed for task: {task.name}')
            return None
        else:
            task_prices[task] = optimal_social_welfare - sum(task.value for task in tasks_prime if task.running_server)
            debug(f'{task.name} Task: £{task_prices[task]:.1f}, Value: {task.value} ', debug_running)

    # Reset the model and allocates all of the their info from the original optimal solution
    reset_model(tasks, servers)
    for task, (s, w, r, server) in task_allocation.items():
        server_task_allocation(server, task, s, w, r, price=task_prices[task])

    return optimal_results


def elastic_vcg_auction(tasks: List[ElasticTask], servers: List[Server], time_limit: Optional[int] = 5,
                        debug_results: bool = False) -> Optional[Result]:
    """
    VCG auction algorithm

    :param tasks: List of tasks
    :param servers: List of servers
    :param time_limit: The time limit of the optimal solver
    :param debug_results: If to debug results
    :return: The results of the VCG auction
    """
    optimal_solver_fn = functools.partial(elastic_optimal_solver, time_limit=time_limit)

    global_model_solution = vcg_solver(tasks, servers, optimal_solver_fn, debug_results)
    if global_model_solution:
        return Result('Elastic VCG Auction', tasks, servers, round(global_model_solution.get_solve_time(), 2),
                      is_auction=True, **{'solve status': global_model_solution.get_solve_status(),
                                          'cplex objective': global_model_solution.get_objective_values()[0]})
    else:
        print(f'Elastic VCG Auction error', file=sys.stderr)
        return Result('Elastic VCG Auction', tasks, servers, 0, limited=True)


def non_elastic_vcg_auction(tasks: List[NonElasticTask], servers: List[Server],
                            time_limit: Optional[int] = 5, debug_results: bool = False) -> Optional[Result]:
    """
    Non-elastic VCG auction algorithm

    :param tasks: List of the Non-elastic tasks
    :param servers: List of servers
    :param time_limit: The limit of the Non-elastic optimal solver
    :param debug_results: If to debug results
    :return: The results of the Non-elastic VCG auction
    """
    non_elastic_solver_fn = functools.partial(non_elastic_optimal_solver, time_limit=time_limit)

    global_model_solution = vcg_solver(tasks, servers, non_elastic_solver_fn, debug_results)
    if global_model_solution:
        return Result('Non-elastic VCG Auction', tasks, servers,
                      round(global_model_solution.get_solve_time(), 2), is_auction=True,
                      **{'solve status': global_model_solution.get_solve_status(),
                         'cplex objective': global_model_solution.get_objective_values()[0]})
    else:
        print(f'Non-elastic VCG Auction error', file=sys.stderr)
        return Result('Non-elastic VCG Auction', tasks, servers, 0, limited=True)
