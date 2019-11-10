"""
Branch and bound algorithm that uses Cplex and domain knowledge to find the optimal solution to the problem case
Lower bound is the current social welfare
Upper bound is the possible sum of all jobs
"""

from __future__ import annotations

from time import time
from typing import List, Dict, Tuple, Optional

from core.job import Job
from core.server import Server
from core.result import Result

from docplex.cp.model import CpoModel, CpoVariable, SOLVE_STATUS_FEASIBLE


def print_allocation(job_server_allocations: Dict[Server, List[Job]]):
    print(', '.join(['{} -> [{}]'.format(server.name, ', '.join([job.name for job in jobs]))
                     for server, jobs in job_server_allocations.items()]))
    
    
def copy(allocation):
    return {server: [job for job in jobs] for server, jobs in allocation.items()}


def feasible_allocation(job_server_allocations: Dict[Server, List[Job]]) -> Optional[Dict[Job, Tuple[int, int, int]]]:
    """
    Checks whether a job to server allocation is a feasible solution to the problem
    :param job_server_allocations: The current job allocation
    :return: An optional dictionary of the job to the tuple of resource speeds
    """
    model = CpoModel("Allocation Feasibility")
    
    loading_speeds: Dict[Job, CpoVariable] = {}
    compute_speeds: Dict[Job, CpoVariable] = {}
    sending_speeds: Dict[Job, CpoVariable] = {}
    
    for server, jobs in job_server_allocations.items():
        for job in jobs:
            loading_speeds[job] = model.integer_var(min=1, max=server.bandwidth_capacity,
                                                    name='Job {} loading speed'.format(job.name))
            compute_speeds[job] = model.integer_var(min=1, max=server.computation_capacity,
                                                    name='Job {} compute speed'.format(job.name))
            sending_speeds[job] = model.integer_var(min=1, max=server.bandwidth_capacity,
                                                    name='Job {} sending speed'.format(job.name))
            
            model.add((job.required_storage / loading_speeds[job]) +
                      (job.required_computation / compute_speeds[job]) +
                      (job.required_results_data / sending_speeds[job]) <= job.deadline)
        
        model.add(sum(job.required_storage for job in jobs) <= server.storage_capacity)
        model.add(sum(compute_speeds[job] for job in jobs) <= server.computation_capacity)
        model.add(sum((loading_speeds[job] + sending_speeds[job]) for job in jobs) <= server.bandwidth_capacity)
    
    model_solution = model.solve(log_output=None)
    if model_solution.get_solve_status() == SOLVE_STATUS_FEASIBLE:
        return {job: (model_solution.get_value(loading_speeds[job]),
                      model_solution.get_value(compute_speeds[job]),
                      model_solution.get_value(sending_speeds[job]))
                for jobs in job_server_allocations.values() for job in jobs}
    else:
        return None


def generate_candidates(allocation: Dict[Server, List[Job]], job: Job, servers: List[Server], pos: int,
                        lower_bound: float, upper_bound: float, best_lower_bound: float,
                        debug_new_candidates: bool = False) -> List[Tuple[float, float, Dict[Server, List[Job]], int]]:
    """
    Generates new candidates of all of the allocations that the job can run on any of the servers
    :param allocation: The allocations of jobs to servers
    :param job: The job
    :param servers: The servers
    :param pos: Job position
    :param lower_bound: The lower bound
    :param upper_bound: The upper bound
    :param best_lower_bound: The best lower bound
    :param debug_new_candidates:
    :return: A list of tuples of the allocation, position, lower bound, upper bound
    """
    
    # All of the new candidates of the job being allocated to a server
    new_candidates = []
    for server in servers:
        allocation_copy = copy(allocation)
        allocation_copy[server].append(job)

        new_candidates.append((lower_bound + job.value, upper_bound, allocation_copy, pos))

        if debug_new_candidates:
            print("New candidates for {} - Lower bound: {}, upper bound: {}, pos: {}"
                  .format(server.name, lower_bound + job.value, upper_bound, pos))
            print_allocation(allocation_copy)
            
    # Non-allocation to a server if the new upper bound is greater than the current best lower bound
    if upper_bound - job.value > best_lower_bound:
        new_candidates.append((lower_bound, upper_bound - job.value, copy(allocation), pos))

        if debug_new_candidates:
            print("New candidates non server - Lower bound: {}, upper bound: {}, pos: {}"
                  .format(lower_bound + job.value, upper_bound, pos))
            print_allocation(allocation)
            
    return new_candidates


def branch_bound_algorithm(jobs: List[Job], servers: List[Server], debug_candidate: bool = True,
                           debug_update_lower_bound: bool = False, debug_feasibility: bool = True) -> Result:
    """
    Branch and bound based algorithm
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param debug_candidate:
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
    candidates: List[Tuple[float, float, Dict[Server, List[Job]], int]] = generate_candidates(
        {server: [] for server in servers}, jobs[0], servers, 1, 0, sum(job.value for job in jobs), best_lower_bound)
    
    # While candidates exist
    while candidates:
        lower_bound, upper_bound, allocation, pos, = candidates.pop(0)
        
        if debug_candidate:
            print("Checking - Lower bound: {}, Upper bound: {}, pos: {}".format(lower_bound, upper_bound, pos))
            print_allocation(allocation)
        
        # Check if the allocation is feasible
        job_speeds = feasible_allocation(allocation)
        if debug_feasibility:
            print("Allocation feasibility: {}".format(job_speeds is not None))
            
        if job_speeds:
            # Update the lower bound if better
            if lower_bound > best_lower_bound:
                if debug_update_lower_bound:
                    print("Update - Lower bound: {}, Best lower bound: {}".format(lower_bound, best_lower_bound))
                
                best_allocation = allocation
                best_speeds = job_speeds
            
            # Generate the new candidates as the allocation was successful
            if pos < len(jobs):
                candidates += generate_candidates(allocation, jobs[pos], servers, pos + 1,
                                                  lower_bound, upper_bound, best_lower_bound)
    
    # Search is finished so allocate the jobs
    for server, allocated_jobs in best_allocation.items():
        for allocated_job in allocated_jobs:
            allocated_job.allocate(best_speeds[allocated_job][0], best_speeds[allocated_job][1],
                                   best_speeds[allocated_job][2], server)
            server.allocate_job(allocated_job)
    
    return Result("Branch & Bound", jobs, servers, time() - start_time)
