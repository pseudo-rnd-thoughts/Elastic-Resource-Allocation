"""Feasible allocations"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docplex.cp.model import CpoModel, CpoVariable
from docplex.cp.solution import SOLVE_STATUS_FEASIBLE

if TYPE_CHECKING:
    from typing import Dict, List, Tuple, Optional
    from core.fixed_task import FixedTask
    from core.server import Server
    from core.task import Task


def flexible_feasible_allocation(task_server_allocations: Dict[Server, List[Task]],
                                 time_limit: int = 60) -> Optional[Dict[Task, Tuple[int, int, int]]]:
    """
    Checks whether a task to server allocation is a feasible solution to the problem

    :param task_server_allocations: The current task allocation
    :param time_limit: The time limit to solve the problem within
    :return: An optional dictionary of the task to the tuple of resource speeds
    """
    model = CpoModel("Allocation Feasibility")

    loading_speeds: Dict[Task, CpoVariable] = {}
    compute_speeds: Dict[Task, CpoVariable] = {}
    sending_speeds: Dict[Task, CpoVariable] = {}

    for server, tasks in task_server_allocations.items():
        for task in tasks:
            loading_speeds[task] = model.integer_var(min=1, max=server.bandwidth_capacity,
                                                     name=f'Job {task.name} loading speed')
            compute_speeds[task] = model.integer_var(min=1, max=server.computation_capacity,
                                                     name=f'Job {task.name} compute speed')
            sending_speeds[task] = model.integer_var(min=1, max=server.bandwidth_capacity,
                                                     name=f'Job {task.name} sending speed')

            model.add((task.required_storage / loading_speeds[task]) +
                      (task.required_computation / compute_speeds[task]) +
                      (task.required_results_data / sending_speeds[task]) <= task.deadline)

        model.add(sum(task.required_storage for task in tasks) <= server.storage_capacity)
        model.add(sum(compute_speeds[task] for task in tasks) <= server.computation_capacity)
        model.add(sum((loading_speeds[task] + sending_speeds[task]) for task in tasks) <= server.bandwidth_capacity)

    model_solution = model.solve(log_output=None, TimeLimit=time_limit)
    if model_solution.get_solve_status() == SOLVE_STATUS_FEASIBLE:
        return {task: (model_solution.get_value(loading_speeds[task]),
                       model_solution.get_value(compute_speeds[task]),
                       model_solution.get_value(sending_speeds[task]))
                for tasks in task_server_allocations.values() for task in tasks}
    else:
        return None


def fixed_feasible_allocation(task_server_allocations: Dict[Server, List[FixedTask]]) \
        -> Optional[Dict[FixedTask, Tuple[int, int, int]]]:
    """
    Checks whether a task to server allocation is a feasible solution to the problem

    :param task_server_allocations: The current task allocation
    :return: An optional dictionary of the task to the tuple of resource speeds
    """
    for server, tasks in task_server_allocations.items():
        if sum(task.required_storage for task in tasks) > server.storage_capacity or \
                sum(task.compute_speed for task in tasks) > server.computation_capacity or \
                sum((task.loading_speed + task.sending_speed) for task in tasks) > server.bandwidth_capacity:
            return None

    return {task: (task.loading_speed, task.compute_speed, task.sending_speed)
            for tasks in task_server_allocations.values() for task in tasks}
