"""
Elastic Optimal algorithms
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from docplex.cp.model import CpoModel
from docplex.cp.solution import SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL, CpoSolveResult
from docplex.cp.solver.solver import CpoSolverException

from src.core.core import server_task_allocation
from src.core.super_server import SuperServer
from src.extra.pprint import print_model_solution, print_model
from src.extra.result import Result

if TYPE_CHECKING:
    from typing import List, Optional

    from src.core.server import Server
    from src.core.elastic_task import ElasticTask


def elastic_optimal_solver(tasks: List[ElasticTask], servers: List[Server], time_limit: Optional[int]):
    """
    Elastic Optimal algorithm solver using cplex

    :param tasks: List of tasks
    :param servers: List of servers
    :param time_limit: Time limit for cplex
    :return: the results of the algorithm
    """
    assert time_limit is None or 0 < time_limit, f'Time limit: {time_limit}'

    model = CpoModel('Elastic Optimal')

    # The resource speed variables and the allocation variables
    loading_speeds, compute_speeds, sending_speeds, task_allocation = {}, {}, {}, {}

    # Loop over each task to allocate the variables and add the deadline constraints
    max_bandwidth = max(server.bandwidth_capacity for server in servers)
    max_computation = max(server.computation_capacity for server in servers)
    runnable_tasks = [task for task in tasks if any(server.can_run_empty(task) for server in servers)]
    for task in runnable_tasks:
        # Check if the task can be run on any server even if empty
        loading_speeds[task] = model.integer_var(min=1, max=max_bandwidth - 1, name=f'{task.name} loading speed')
        compute_speeds[task] = model.integer_var(min=1, max=max_computation, name=f'{task.name} compute speed')
        sending_speeds[task] = model.integer_var(min=1, max=max_bandwidth - 1, name=f'{task.name} sending speed')

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
                      for task in runnable_tasks) <= server.available_storage)
        model.add(sum(compute_speeds[task] * task_allocation[(task, server)]
                      for task in runnable_tasks) <= server.available_computation)
        model.add(sum((loading_speeds[task] + sending_speeds[task]) * task_allocation[(task, server)]
                      for task in runnable_tasks) <= server.available_bandwidth)

    # The optimisation statement
    model.maximize(sum(task.value * task_allocation[(task, server)] for task in runnable_tasks for server in servers))

    # Solve the cplex model with time limit
    try:
        model_solution: CpoSolveResult = model.solve(log_output=None, TimeLimit=time_limit)
    except CpoSolverException as e:
        print(f'Solver Exception: ', e)
        return None

    # Check that it is solved
    if model_solution.get_solve_status() != SOLVE_STATUS_FEASIBLE and \
            model_solution.get_solve_status() != SOLVE_STATUS_OPTIMAL:
        print(f'Optimal solver failed', file=sys.stderr)
        print_model_solution(model_solution)
        print_model(tasks, servers)
        return None

    # Generate the allocation of the tasks and servers
    try:
        for task in runnable_tasks:
            for server in servers:
                if model_solution.get_value(task_allocation[(task, server)]):
                    server_task_allocation(server, task,
                                           model_solution.get_value(loading_speeds[task]),
                                           model_solution.get_value(compute_speeds[task]),
                                           model_solution.get_value(sending_speeds[task]))
                    break

        if abs(model_solution.get_objective_values()[0] - sum(t.value for t in tasks if t.running_server)) > 0.1:
            print('Elastic optimal different objective values - '
                  f'cplex: {model_solution.get_objective_values()[0]} and '
                  f'running task values: {sum(task.value for task in tasks if task.running_server)}', file=sys.stderr)
        return model_solution
    except (AssertionError, KeyError) as e:
        print('Error: ', e, file=sys.stderr)
        print_model_solution(model_solution)


def elastic_optimal(tasks: List[ElasticTask], servers: List[Server],
                    time_limit: Optional[int] = 15) -> Optional[Result]:
    """
    Runs the optimal task allocation algorithm solver for the time limit given the list of tasks and servers

    :param tasks: List of tasks
    :param servers: List of servers
    :param time_limit: The time limit for the cplex solver
    :return: Optimal results find setting is valid
    """
    model_solution = elastic_optimal_solver(tasks, servers, time_limit)
    if model_solution:
        return Result('Elastic Optimal', tasks, servers, round(model_solution.get_solve_time(), 2),
                      **{'solve status': model_solution.get_solve_status(),
                         'cplex objective': model_solution.get_objective_values()[0]})
    else:
        print(f'Elastic Optimal error', file=sys.stderr)
        return Result('Elastic Optimal', tasks, servers, 0, limited=True)


def server_relaxed_elastic_optimal(tasks: List[ElasticTask], servers: List[Server],
                                   time_limit: Optional[int] = 15) -> Optional[Result]:
    """
    Runs the relaxed task allocation solver

    :param tasks: List of tasks
    :param servers: List of servers
    :param time_limit: The time limit for the solver
    :return: Optional relaxed results
    """
    super_server = SuperServer(servers)
    model_solution = elastic_optimal_solver(tasks, [super_server], time_limit)
    if model_solution:
        return Result('Server Relaxed Elastic Optimal', tasks, [super_server],
                      round(model_solution.get_solve_time(), 2),
                      **{'solve status': model_solution.get_solve_status(),
                         'cplex objective': model_solution.get_objective_values()[0]})
    else:
        print(f'Server Relaxed Elastic Optimal error', file=sys.stderr)
        return Result('Server Relaxed Elastic Optimal', tasks, servers, 0, limited=True)
