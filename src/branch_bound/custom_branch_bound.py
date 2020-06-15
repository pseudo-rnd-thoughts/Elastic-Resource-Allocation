"""
Branch and bound algorithm that uses Cplex and domain knowledge to find the optimal solution to the problem case

Lower bound is the current social welfare, Upper bound is the possible sum of all tasks
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docplex.cp.model import CpoModel, CpoVariable, SOLVE_STATUS_FEASIBLE

from core.result import Result

if TYPE_CHECKING:
    from typing import List, Dict, Tuple, Optional

    from core.task import Task
    from core.server import Server


def feasible_allocation(task_server_allocations: Dict[Server, List[Task]]) \
        -> Optional[Dict[Task, Tuple[int, int, int]]]:
    """
    Checks whether a task to server allocation is a feasible solution to the problem

    :param task_server_allocations: Current task server allocation
    :return: If valid solution exists then return allocation
    """
    model = CpoModel('Allocation Feasibility')

    loading_speeds: Dict[Task, CpoVariable] = {}
    compute_speeds: Dict[Task, CpoVariable] = {}
    sending_speeds: Dict[Task, CpoVariable] = {}

    for server, tasks in task_server_allocations.items():
        for task in tasks:
            loading_speeds[task] = model.integer_var(min=1, max=server.bandwidth_capacity,
                                                     name=f'Task {task.name} loading speed')
            compute_speeds[task] = model.integer_var(min=1, max=server.computation_capacity,
                                                     name=f'Task {task.name} compute speed')
            sending_speeds[task] = model.integer_var(min=1, max=server.bandwidth_capacity,
                                                     name=f'Task {task.name} sending speed')

            model.add((task.required_storage / loading_speeds[task]) +
                      (task.required_computation / compute_speeds[task]) +
                      (task.required_results_data / sending_speeds[task]) <= task.deadline)

        model.add(sum(task.required_storage for task in tasks) <= server.storage_capacity)
        model.add(sum(compute_speeds[task] for task in tasks) <= server.computation_capacity)
        model.add(sum((loading_speeds[task] + sending_speeds[task]) for task in tasks) <= server.bandwidth_capacity)

    model_solution = model.solve(log_context=None)
    if model_solution.get_search_status() == SOLVE_STATUS_FEASIBLE:
        return {
            task: (model_solution.get_value(loading_speeds[task]), model_solution.get_value(compute_speeds[task]),
                   model_solution.get_value(sending_speeds[task]))
            for tasks in task_server_allocations.values() for task in tasks
        }
    else:
        return None


def generate_candidates(allocation: Dict[Server, List[Task]], task: Task, servers: List[Server], pos: int,
                        lower_bound: float, upper_bound: float,
                        best_lower_bound: float) -> List[Tuple[float, float, Dict[Server, List[Task]], int]]:
    """
    Generates all of the candidates from a prior allocation using the list of tasks and servers
    using the current position in the task list for which tasks to use

    :param allocation: Current allocation
    :param task: List of tasks
    :param servers: List of servers
    :param pos: Position
    :param lower_bound: Lower bound
    :param upper_bound: Upper bound
    :param best_lower_bound: Current best lower bound
    :return: A list of tuples of the allocation, position, lower bound, upper bound
    """
    new_candidates = []
    for server in servers:
        allocation_copy = allocation.copy()
        allocation[server].append(task)

        new_candidates.append((lower_bound + task.value, upper_bound, allocation_copy, pos))

    if upper_bound - task.value > best_lower_bound:
        new_candidates.append((lower_bound, upper_bound - task.value, allocation.copy(), pos))

    return new_candidates


def branch_bound(tasks: List[Task], servers: List[Server]) -> Result:
    """
    Run branch and bound

    :param tasks: List of tasks
    :param servers: List of servers
    :return: New results
    """
    best_lower_bound: float = 0
    best_allocation: Optional[Dict[Server, List[Task]]] = None
    best_speeds: Optional[Dict[Task, Tuple[int, int, int]]] = None

    candidates: List[Tuple[float, float, Dict[Server, List[Task]], int]] = generate_candidates(
        {server: [] for server in servers}, tasks[0], servers, 1, 0, sum(task.value for task in tasks),
        best_lower_bound)

    while candidates:
        lower_bound, upper_bound, allocation, pos, = candidates.pop(0)

        task_speeds = feasible_allocation(allocation)
        if task_speeds:
            if lower_bound > best_lower_bound:
                best_allocation = allocation
                best_speeds = task_speeds

            new_candidates = generate_candidates(allocation, tasks[pos], servers, pos + 1,
                                                 lower_bound, upper_bound, best_lower_bound)
            for new_candidate in new_candidates:
                candidates.append(new_candidate)

    for server, allocated_tasks in best_allocation.items():
        for allocated_task in allocated_tasks:
            allocated_task.allocate(best_speeds[allocated_task][0], best_speeds[allocated_task][1],
                                    best_speeds[allocated_task][2], server)
            server.allocate_task(allocated_task)

    return Result('Branch & Bound', tasks, servers, 0)
