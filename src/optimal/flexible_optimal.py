"""
Optimal algorithms
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from docplex.cp.model import CpoModel, CpoVariable
from docplex.cp.solution import SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL

from extra.visualise import minimise_resource_allocation
from src.core.core import server_task_allocation
from src.extra.pprint import print_model_solution, print_model
from src.extra.result import Result

if TYPE_CHECKING:
    from typing import List, Dict, Tuple, Optional

    from src.core.server import Server
    from src.core.task import Task


# noinspection DuplicatedCode
def flexible_optimal_solver(tasks: List[Task], servers: List[Server], time_limit: int):
    """
    Optimal algorithm

    :param tasks: List of tasks
    :param servers: List of servers
    :param time_limit: Time limit for cplex
    :return: the results of the algorithm
    """
    assert 0 < time_limit, f'Time limit: {time_limit}'

    model = CpoModel('Flexible Optimal')

    # The resource speed variables and the allocation variables
    loading_speeds: Dict[Task, CpoVariable] = {}
    compute_speeds: Dict[Task, CpoVariable] = {}
    sending_speeds: Dict[Task, CpoVariable] = {}
    task_allocation: Dict[Tuple[Task, Server], CpoVariable] = {}

    # The maximum bandwidth and the computation that the speed can be
    max_bandwidth = max(server.available_bandwidth for server in servers) - 1
    max_computation = max(server.available_computation for server in servers)

    # Loop over each task to allocate the variables and add the deadline constraints
    for task in tasks:
        loading_speeds[task] = model.integer_var(min=1, max=max_bandwidth, name=f'{task.name} loading speed')
        compute_speeds[task] = model.integer_var(min=1, max=max_computation, name=f'{task.name} compute speed')
        sending_speeds[task] = model.integer_var(min=1, max=max_bandwidth, name=f'{task.name} sending speed')

        model.add((task.required_storage / loading_speeds[task]) +
                  (task.required_computation / compute_speeds[task]) +
                  (task.required_results_data / sending_speeds[task]) <= task.deadline)

        # The task allocation variables and add the allocation constraint
        for server in servers:
            task_allocation[(task, server)] = model.binary_var(name=f'{task.name} Task - {server.name} Server')
        model.add(sum(task_allocation[(task, server)] for server in servers) <= 1)

    # For each server, add the resource constraint
    for server in servers:
        model.add(sum(task.required_storage * task_allocation[(task, server)]
                      for task in tasks) <= server.available_storage)
        model.add(sum(compute_speeds[task] * task_allocation[(task, server)]
                      for task in tasks) <= server.available_computation)
        model.add(sum((loading_speeds[task] + sending_speeds[task]) * task_allocation[(task, server)]
                      for task in tasks) <= server.available_bandwidth)

    # The optimisation statement
    model.maximize(sum(task.value * task_allocation[(task, server)] for task in tasks for server in servers))

    # Solve the cplex model with time limit
    model_solution = model.solve(log_output=None, TimeLimit=time_limit)

    # Check that it is solved
    if model_solution.get_solve_status() != SOLVE_STATUS_FEASIBLE and \
            model_solution.get_solve_status() != SOLVE_STATUS_OPTIMAL:
        print(f'Optimal solver failed')
        print_model_solution(model_solution)
        print_model(tasks, servers)
        return None

    # Generate the allocation of the tasks and servers
    try:
        for task in tasks:
            for server in servers:
                if model_solution.get_value(task_allocation[(task, server)]):
                    server_task_allocation(server, task,
                                           model_solution.get_value(loading_speeds[task]),
                                           model_solution.get_value(compute_speeds[task]),
                                           model_solution.get_value(sending_speeds[task]))
    except (AssertionError, KeyError) as e:
        print('Error: ', e)
        print_model_solution(model_solution)
        return None

    return model_solution


def minimal_flexible_optimal_solver(tasks: List[Task], servers: List[Server],
                                    solver_time_limit: int, minimise_time_limit: int = 2):
    """
    Minimise the resources used by flexible optimal solver

    :param tasks: List of tasks
    :param servers: List of servers
    :param solver_time_limit: Solver time limit
    :param minimise_time_limit: Minimise solver time limit
    """
    flexible_optimal_solver(tasks, servers, solver_time_limit)
    minimise_resource_allocation(tasks, servers, minimise_time_limit)


def flexible_optimal(tasks: List[Task], servers: List[Server], time_limit: int = 15) -> Optional[Result]:
    """
    Runs the optimal task allocation algorithm solver

    :param tasks: List of tasks
    :param servers: List of servers
    :param time_limit: The time limit for the cplex solver
    :return: Optional optimal results
    """
    model_solution = flexible_optimal_solver(tasks, servers, time_limit=time_limit)
    if model_solution:
        return Result('Flexible Optimal', tasks, servers, round(model_solution.get_solve_time(), 2),
                      **{'solve status': model_solution.get_solve_status()})
    else:
        print(f'Flexible Optimal error', file=sys.stderr)
        return Result('Optimal', tasks, servers, 0, limited=True)
