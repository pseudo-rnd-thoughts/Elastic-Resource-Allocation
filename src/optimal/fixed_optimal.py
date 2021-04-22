"""
Fixed optimal algorithm
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from docplex.cp.model import CpoModel
from docplex.cp.solution import SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL

from src.core.core import server_task_allocation
from src.core.fixed_task import FixedTask
from src.extra.pprint import print_model_solution
from src.extra.result import Result

if TYPE_CHECKING:
    from typing import List, Optional

    from src.core.server import Server


def fixed_optimal_solver(tasks: List[FixedTask], servers: List[Server], time_limit: Optional[int]):
    """
    Finds the optimal solution

    :param tasks: A list of tasks
    :param servers: A list of servers
    :param time_limit: The time limit to solve with
    :return: The results
    """
    assert time_limit is None or 0 < time_limit, f'Time limit: {time_limit}'

    model = CpoModel('vcg')

    # As no resource speeds then only assign binary variables for the allocation
    allocations = {(task, server): model.binary_var(name=f'{task.name} task {server.name} server')
                   for task in tasks for server in servers}

    # Allocation constraint
    for task in tasks:
        model.add(sum(allocations[(task, server)] for server in servers) <= 1)

    # Server resource speeds constraints
    for server in servers:
        model.add(sum(task.required_storage * allocations[(task, server)]
                      for task in tasks) <= server.available_storage)
        model.add(sum(task.compute_speed * allocations[(task, server)]
                      for task in tasks) <= server.available_computation)
        model.add(sum((task.loading_speed + task.sending_speed) * allocations[(task, server)]
                      for task in tasks) <= server.available_bandwidth)

    # Optimisation problem
    model.maximize(sum(task.value * allocations[(task, server)] for task in tasks for server in servers))

    # Solve the cplex model with time limit
    model_solution = model.solve(log_output=None, TimeLimit=time_limit)

    # Check that the model is solved
    if model_solution.get_solve_status() != SOLVE_STATUS_FEASIBLE and \
            model_solution.get_solve_status() != SOLVE_STATUS_OPTIMAL:
        print('Fixed optimal failure', file=sys.stderr)
        print_model_solution(model_solution)
        return None

    # Allocate all of the tasks to the servers
    try:
        for task in tasks:
            for server in servers:
                if model_solution.get_value(allocations[(task, server)]):
                    server_task_allocation(server, task, task.loading_speed, task.compute_speed, task.sending_speed)
                    break

        if abs(model_solution.get_objective_values()[0] - sum(t.value for t in tasks if t.running_server)) > 0.1:
            print('Fixed optimal different objective values - '
                  f'cplex: {model_solution.get_objective_values()[0]} and '
                  f'running task values: {sum(task.value for task in tasks if task.running_server)}', file=sys.stderr)
    except (KeyError, AssertionError) as e:
        print('Assertion error in fixed optimal algorithm: ', e, file=sys.stderr)
        print_model_solution(model_solution)
        return None

    return model_solution


def fixed_optimal(tasks: List[FixedTask], servers: List[Server], time_limit: Optional[int] = 15) -> Optional[Result]:
    """
    Runs the fixed optimal cplex algorithm solver with a time limit

    :param tasks: List of fixed tasks
    :param servers: List of servers
    :param time_limit: Cplex time limit
    :return: Optional results
    """
    model_solution = fixed_optimal_solver(tasks, servers, time_limit=time_limit)
    if model_solution:
        return Result('Fixed Optimal', tasks, servers, round(model_solution.get_solve_time(), 2),
                      **{'solve status': model_solution.get_solve_status(),
                         'cplex objective': model_solution.get_objective_values()[0]})
    else:
        print(f'Fixed optimal error', file=sys.stderr)
        return Result('Fixed Optimal', tasks, servers, 0, limited=True)


def foreknowledge_fixed_optimal(tasks: List[FixedTask], servers: List[Server],
                                time_limit: Optional[int] = 15) -> Optional[Result]:
    """
    Runs the foreknowledge fixed optimal cplex algorithm solver with a time limit

    :param tasks: List of fixed tasks
    :param servers: List of servers
    :param time_limit: Cplex time limit
    :return: Optional results
    """
    model_solution = fixed_optimal_solver(tasks, servers, time_limit=time_limit)
    if model_solution:
        return Result('Foreknowledge Fixed Optimal', tasks, servers, round(model_solution.get_solve_time(), 2),
                      **{'solve status': model_solution.get_solve_status(),
                         'cplex objective': model_solution.get_objective_values()[0]})
    else:
        print(f'Foreknowledge Fixed optimal error', file=sys.stderr)
        return Result('Foreknowledge Fixed Optimal', tasks, servers, 0, limited=True)
