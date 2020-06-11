"""
Branch and bound algorithm that uses Cplex and domain knowledge to find the optimal solution to the problem case
Lower bound is the current social welfare
Upper bound is the possible sum of all jobs
"""

from __future__ import annotations

from typing import List, Dict, Tuple, Optional

from docplex.cp.model import CpoModel, CpoVariable, SOLVE_STATUS_FEASIBLE

from src.core.task import Task
from src.core.result import Result
from src.core.server import Server


def feasible_allocation(job_server_allocations: Dict[Server, List[Task]]) -> Optional[Dict[Task, Tuple[int, int, int]]]:
    """
    Checks whether a job to server allocation is a feasible solution to the problem

    :param job_server_allocations: Current job server allocation
    :return: If valid solution exists then return allocation
    """
    model = CpoModel("Allocation Feasibility")

    loading_speeds: Dict[Task, CpoVariable] = {}
    compute_speeds: Dict[Task, CpoVariable] = {}
    sending_speeds: Dict[Task, CpoVariable] = {}

    for server, jobs in job_server_allocations.items():
        for job in jobs:
            loading_speeds[job] = model.integer_var(min=1, max=server.bandwidth_capacity,
                                                    name='Task {} loading speed'.format(job.name))
            compute_speeds[job] = model.integer_var(min=1, max=server.computation_capacity,
                                                    name='Task {} compute speed'.format(job.name))
            sending_speeds[job] = model.integer_var(min=1, max=server.bandwidth_capacity,
                                                    name='Task {} sending speed'.format(job.name))

            model.add((job.required_storage / loading_speeds[job]) +
                      (job.required_computation / compute_speeds[job]) +
                      (job.required_results_data / sending_speeds[job]) <= job.deadline)

        model.add(sum(job.required_storage for job in jobs) <= server.storage_capacity)
        model.add(sum(compute_speeds[job] for job in jobs) <= server.computation_capacity)
        model.add(sum((loading_speeds[job] + sending_speeds[job]) for job in jobs) <= server.bandwidth_capacity)

    model_solution = model.solve(log_context=None)
    if model_solution.get_search_status() == SOLVE_STATUS_FEASIBLE:
        return {job: (model_solution.get_value(loading_speeds[job]), model_solution.get_value(compute_speeds[job]),
                      model_solution.get_value(sending_speeds[job]))
                for jobs in job_server_allocations.values() for job in jobs}
    else:
        return None


def generate_candidates(allocation: Dict[Server, List[Task]], job: Task, servers: List[Server], pos: int,
                        lower_bound: float, upper_bound: float,
                        best_lower_bound: float) -> List[Tuple[float, float, Dict[Server, List[Task]], int]]:
    """
    Generates all of the candidates from a prior allocation using the list of jobs and servers
    using the current position in the job list for which jobs to use

    :param allocation: Current allocation
    :param job: List of jobs
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
        allocation[server].append(job)

        new_candidates.append((lower_bound + job.value, upper_bound, allocation_copy, pos))

    if upper_bound - job.value > best_lower_bound:
        new_candidates.append((lower_bound, upper_bound - job.value, allocation.copy(), pos))

    return new_candidates


def branch_bound(jobs: List[Task], servers: List[Server]) -> Result:
    """
    Run branch and bound

    :param jobs: List of jobs
    :param servers: List of servers
    :return: New results
    """
    best_lower_bound: float = 0
    best_allocation: Optional[Dict[Server, List[Task]]] = None
    best_speeds: Optional[Dict[Task, Tuple[int, int, int]]] = None

    candidates: List[Tuple[float, float, Dict[Server, List[Task]], int]] = generate_candidates(
        {server: [] for server in servers}, jobs[0], servers, 1, 0, sum(job.value for job in jobs), best_lower_bound)

    while candidates:
        lower_bound, upper_bound, allocation, pos, = candidates.pop(0)

        job_speeds = feasible_allocation(allocation)
        if job_speeds:
            if lower_bound > best_lower_bound:
                best_allocation = allocation
                best_speeds = job_speeds

            new_candidates = generate_candidates(allocation, jobs[pos], servers, pos + 1,
                                                 lower_bound, upper_bound, best_lower_bound)
            for new_candidate in new_candidates:
                candidates.append(new_candidate)

    for server, allocated_jobs in best_allocation.items():
        for allocated_job in allocated_jobs:
            allocated_job.allocate(best_speeds[allocated_job][0], best_speeds[allocated_job][1],
                                   best_speeds[allocated_job][2], server)
            server.allocate_job(allocated_job)

    return Result("Branch & Bound", jobs, servers, 0)
