"""
Branch and bound algorithm that uses Cplex and domain knowledge to find the optimal solution to the problem case
Lower bound is the current social welfare
Upper bound is the possible sum of all jobs
"""

from __future__ import annotations

from time import time
from typing import List, Dict, Tuple, Optional

from branch_bound.feasibility_allocations import flexible_feasible_allocation
from branch_bound.priority_queue import Comparison, PriorityQueue
from core.fixed_job import FixedJob
from core.job import Job
from core.server import Server
from core.result import Result

from docplex.cp.model import CpoModel, CpoVariable, SOLVE_STATUS_FEASIBLE


def print_allocation(job_server_allocations: Dict[Server, List[Job]]):
    print(', '.join(['{} -> [{}]'.format(server.name, ', '.join([job.name for job in jobs]))
                     for server, jobs in job_server_allocations.items()]))


def copy(allocation):
    return {server: [job for job in jobs] for server, jobs in allocation.items()}


def generate_candidates(allocation: Dict[Server, List[Job]], jobs: List[Job], servers: List[Server], pos: int,
                        lower_bound: float, upper_bound: float,
                        debug_new_candidates: bool = False) -> List[Tuple[float, float, Dict[Server, List[Job]], int]]:
    """
    Generates new candidates of all of the allocations that the job can run on any of the servers
    :param allocation: The allocations of jobs to servers
    :param jobs: List of the jobs
    :param servers: List of the servers
    :param pos: Job position
    :param lower_bound: The lower bound
    :param upper_bound: The upper bound
    :param debug_new_candidates:
    :return: A list of tuples of the allocation, position, lower bound, upper bound
    """
    if len(jobs) <= pos:
        return []

    # All of the new candidates of the job being allocated to a server
    new_candidates = []
    job = jobs[pos]
    for server in servers:
        allocation_copy = copy(allocation)
        allocation_copy[server].append(job)

        new_candidates.append((lower_bound + job.value, upper_bound, allocation_copy, pos + 1))

        if debug_new_candidates:
            print("New candidates for {} - Lower bound: {}, upper bound: {}, pos: {}"
                  .format(server.name, lower_bound + job.value, upper_bound, pos + 1))
            print_allocation(allocation_copy)

    # Non-allocation to a server if the new upper bound is greater than the current best lower bound
    new_candidates += generate_candidates(allocation, jobs, servers, pos + 1, lower_bound, upper_bound - job.value,
                                          debug_new_candidates=debug_new_candidates)

    return new_candidates


def branch_bound_algorithm(jobs: List[Job], servers: List[Server], feasibility=flexible_feasible_allocation,
                           debug_new_candidate: bool = False, debug_checking_allocation: bool = False,
                           debug_update_lower_bound: bool = False, debug_feasibility: bool = False) -> Result:
    """
    Branch and bound based algorithm
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param feasibility: Feasibility function
    :param debug_new_candidate:
    :param debug_checking_allocation:
    :param debug_update_lower_bound:
    :param debug_feasibility:
    :return: The results from the search
    """
    start_time = time()

    # The best values for the lower bound, allocation and speeds
    best_lower_bound: float = 0
    best_allocation: Optional[Dict[Server, List[Job]]] = None
    best_speeds: Optional[Dict[Job, Tuple[int, int, int]]] = None

    # Generates the initial candidates
    def compare(candidate_1, candidate_2):
        return Comparison.compare(candidate_1[0], candidate_2[0])

    def evaluate(candidate):
        return str(candidate[0])

    candidates = PriorityQueue(compare, evaluate)
    candidates.push_all(generate_candidates({server: [] for server in servers}, jobs, servers, 0, 0,
                                            sum(job.value for job in jobs), debug_new_candidates=debug_new_candidate))

    # While candidates exist
    while candidates.size > 0:
        actual_lower_bound = max(candidate[0] for candidate in candidates.queue)
        lower_bound, upper_bound, allocation, pos = candidates.pop()
        assert actual_lower_bound == lower_bound

        if best_lower_bound < upper_bound:
            if debug_checking_allocation:
                print("Checking - Lower bound: {}, Upper bound: {}, pos: {}".format(lower_bound, upper_bound, pos))
                print_allocation(allocation)

            # Check if the allocation is feasible
            job_speeds = feasibility(allocation)
            if debug_feasibility:
                print("Allocation feasibility: {}".format(job_speeds is not None))

            if job_speeds:
                # Update the lower bound if better
                if best_lower_bound < lower_bound:
                    if debug_update_lower_bound:
                        print("Update - New Lower bound: {}".format(lower_bound))

                    best_allocation = allocation
                    best_speeds = job_speeds
                    best_lower_bound = lower_bound

                # Generate the new candidates as the allocation was successful
                if pos < len(jobs):
                    candidates.push_all(generate_candidates(allocation, jobs, servers, pos, lower_bound, upper_bound,
                                                            debug_new_candidates=debug_new_candidate))

    # Search is finished so allocate the jobs
    for server, allocated_jobs in best_allocation.items():
        for allocated_job in allocated_jobs:
            allocated_job.allocate(best_speeds[allocated_job][0], best_speeds[allocated_job][1],
                                   best_speeds[allocated_job][2], server)
            server.allocate_job(allocated_job)

    return Result("Branch & Bound", jobs, servers, time() - start_time)
