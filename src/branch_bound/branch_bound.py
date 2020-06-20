"""
Branch and bound algorithm that uses Cplex and domain knowledge to find the optimal solution to the problem case

Lower bound is the current social welfare, Upper bound is the possible sum of all tasks
"""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING

from branch_bound.feasibility_allocations import flexible_feasible_allocation
from branch_bound.priority_queue import Comparison, PriorityQueue
from extra.pprint import print_allocation
from extra.result import Result

if TYPE_CHECKING:
    from typing import List, Dict, Tuple, Optional
    from core.server import Server
    from core.task import Task


def copy(allocation):
    """
    Copy the allocation

    :param allocation: The allocation
    :return: Copy of the allocation parameter
    """
    return {server: [task for task in tasks] for server, tasks in allocation.items()}


def generate_candidates(allocation: Dict[Server, List[Task]], tasks: List[Task], servers: List[Server], pos: int,
                        lower_bound: float, upper_bound: float,
                        debug_new_candidates: bool = False) -> List[Tuple[float, float, Dict[Server, List[Task]], int]]:
    """
    Generates new candidates of all of the allocations that the task can run on any of the servers

    :param allocation: The allocations of tasks to servers
    :param tasks: List of the tasks
    :param servers: List of the servers
    :param pos: Job position
    :param lower_bound: The lower bound
    :param upper_bound: The upper bound
    :param debug_new_candidates:
    :return: A list of tuples of the allocation, position, lower bound, upper bound
    """
    if len(tasks) <= pos:
        return []

    # All of the new candidates of the task being allocated to a server
    new_candidates = []
    task = tasks[pos]
    for server in servers:
        allocation_copy = copy(allocation)
        allocation_copy[server].append(task)

        new_candidates.append((lower_bound + task.value, upper_bound, allocation_copy, pos + 1))

        if debug_new_candidates:
            print(f'New candidates for {server.name} - Lower bound: {lower_bound + task.value}, '
                  f'upper bound: {upper_bound}, pos: {pos + 1}')
            print_allocation(allocation_copy)

    # Non-allocation to a server if the new upper bound is greater than the current best lower bound
    new_candidates += generate_candidates(allocation, tasks, servers, pos + 1, lower_bound, upper_bound - task.value,
                                          debug_new_candidates=debug_new_candidates)

    return new_candidates


def branch_bound_algorithm(tasks: List[Task], servers: List[Server], feasibility=flexible_feasible_allocation,
                           debug_new_candidate: bool = False, debug_checking_allocation: bool = False,
                           debug_update_lower_bound: bool = False, debug_feasibility: bool = False) -> Result:
    """
    Branch and bound based algorithm

    :param tasks: A list of tasks
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
    best_allocation: Optional[Dict[Server, List[Task]]] = None
    best_speeds: Optional[Dict[Task, Tuple[int, int, int]]] = None

    # Generates the initial candidates
    def compare(candidate_1, candidate_2):
        """
        Compare two candidates

        :param candidate_1: Candidate 1
        :param candidate_2: Candidate 2
        :return: The comparison between the two
        """
        return Comparison.compare(candidate_1[0], candidate_2[0])

    def evaluate(candidate):
        """
        Evaluate the candidate

        :param candidate: The candidate
        :return: String for the candidate
        """
        return str(candidate[0])

    candidates = PriorityQueue(compare, evaluate)
    candidates.push_all(generate_candidates({server: [] for server in servers}, tasks, servers, 0, 0,
                                            sum(task.value for task in tasks),
                                            debug_new_candidates=debug_new_candidate))

    # While candidates exist
    while candidates.size > 0:
        actual_lower_bound = max(candidate[0] for candidate in candidates.queue)
        lower_bound, upper_bound, allocation, pos = candidates.pop()
        assert actual_lower_bound == lower_bound

        if best_lower_bound < upper_bound:
            if debug_checking_allocation:
                print(f'Checking - Lower bound: {lower_bound}, Upper bound: {upper_bound}, pos: {pos}')
                # print_allocation(allocation)

            # Check if the allocation is feasible
            task_speeds = feasibility(allocation)
            if debug_feasibility:
                print(f'Allocation feasibility: {task_speeds is not None}')

            if task_speeds:
                # Update the lower bound if better
                if best_lower_bound < lower_bound:
                    if debug_update_lower_bound:
                        print(f'Update - New Lower bound: {lower_bound}')

                    best_allocation = allocation
                    best_speeds = task_speeds
                    best_lower_bound = lower_bound

                # Generate the new candidates as the allocation was successful
                if pos < len(tasks):
                    candidates.push_all(generate_candidates(allocation, tasks, servers, pos, lower_bound, upper_bound,
                                                            debug_new_candidates=debug_new_candidate))

    # Search is finished so allocate the tasks
    for server, allocated_tasks in best_allocation.items():
        for allocated_task in allocated_tasks:
            allocated_task.allocate(best_speeds[allocated_task][0], best_speeds[allocated_task][1],
                                    best_speeds[allocated_task][2], server)
            server.allocate_task(allocated_task)

    return Result('Branch & Bound', tasks, servers, time() - start_time)
