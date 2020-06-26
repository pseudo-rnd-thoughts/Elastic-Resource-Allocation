"""
Relaxed model with a single super server allow a upper bound to be found, solved through mixed integer programming
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from docplex.cp.model import CpoModel, CpoVariable
from docplex.cp.solution import CpoSolveResult
from docplex.cp.solution import SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL

from core.core import server_task_allocation
from extra.pprint import print_model_solution, print_model
from extra.result import Result

if TYPE_CHECKING:
    from typing import List, Dict

    from core.server import Server
    from core.super_server import SuperServer
    from core.task import Task


def relaxed_solver(tasks: List[Task], servers: List[Server], time_limit: int, debug_time: bool = False):
    """
    Runs the optimal algorithm solution

    :param tasks: A list of tasks
    :param servers: A list of servers
    :param time_limit: The time limit to solve
    :param debug_time: If to print the time taken
    :return: The result from optimal solution
    """
    assert 0 < time_limit
    model = CpoModel('Server Job Allocation')

    loading_speeds: Dict[Task, CpoVariable] = {}
    compute_speeds: Dict[Task, CpoVariable] = {}
    sending_speeds: Dict[Task, CpoVariable] = {}
    task_allocation: Dict[Task, CpoVariable] = {}

    super_server = SuperServer(servers)

    for task in tasks:
        loading_speeds[task] = model.integer_var(min=1, max=super_server.bandwidth_capacity)
        compute_speeds[task] = model.integer_var(min=1, max=super_server.computation_capacity)
        sending_speeds[task] = model.integer_var(min=1, max=super_server.bandwidth_capacity)
        task_allocation[task] = model.binary_var(name=f'{task.name} allocation')

        model.add(task.required_storage / loading_speeds[task] +
                  task.required_computation / compute_speeds[task] +
                  task.required_results_data / sending_speeds[task] <= task.deadline)

    model.add(sum(task.required_storage * task_allocation[task] for task in tasks) <= super_server.storage_capacity)
    model.add(sum(compute_speeds[task] * task_allocation[task] for task in tasks) <= super_server.computation_capacity)
    model.add(sum((loading_speeds[task] + sending_speeds[task]) * task_allocation[task] for task in
                  tasks) <= super_server.bandwidth_capacity)

    model.maximize(sum(task.value * task_allocation[task] for task in tasks))

    # Run the model
    model_solution: CpoSolveResult = model.solve(log_output=None, RelativeOptimalityTolerance=0.01,
                                                 TimeLimit=time_limit)
    if debug_time:
        print(f'Solve time: {round(model_solution.get_solve_time(), 2)} secs, '
              f'Objective value: {model_solution.get_objective_values()}, '
              f'bounds: {model_solution.get_objective_bounds()}, gaps: {model_solution.get_objective_gaps()}')

    # Check that it is solved
    if model_solution.get_solve_status() != SOLVE_STATUS_FEASIBLE and \
            model_solution.get_solve_status() != SOLVE_STATUS_OPTIMAL:
        print('Optimal algorithm failed')
        print_model_solution(model_solution)
        print_model(tasks, servers)
        return None

    # For each of the tasks allocate if allocated to the server
    for task in tasks:
        if model_solution.get_value(task_allocation[task]):
            server_task_allocation(super_server, task,
                                   model_solution.get_value(loading_speeds[task]),
                                   model_solution.get_value(compute_speeds[task]),
                                   model_solution.get_value(sending_speeds[task]))
    return model_solution, super_server


def relaxed(tasks: List[Task], servers: List[Server], time_limit: int) -> Optional[Result]:
    """
    Runs the relaxed task allocation solver

    :param tasks: List of tasks
    :param servers: List of servers
    :param time_limit: The time limit for the solver
    :return: Optional relaxed results
    """
    model_solution, super_server = relaxed_solver(tasks, servers, time_limit=time_limit)
    if model_solution:
        return Result('Relaxed', tasks, [super_server], round(model_solution.get_solve_time(), 2),
                      **{'solve status': model_solution.get_solve_status()})
