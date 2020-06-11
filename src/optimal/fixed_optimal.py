"""Fixed optimal algorithm"""

from __future__ import annotations

from typing import List, Optional

from docplex.cp.model import CpoModel
from docplex.cp.solution import SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL

from src.core.core import print_model_solution, allocate
from src.core.fixed_task import FixedTask
from src.core.result import Result
from src.core.server import Server


def fixed_optimal_algorithm(jobs: List[FixedTask], servers: List[Server], time_limit: int) -> Optional[Result]:
    """
    Finds the optimal solution

    :param jobs: A list of jobs
    :param servers: A list of servers
    :param time_limit: The time limit to solve with
    :return: The results
    """
    assert time_limit > 0, "Time limit: {}".format(time_limit)

    model = CpoModel("vcg")

    # As no resource speeds then only assign binary variables for the allocation
    allocations = {(job, server): model.binary_var(name='{} job {} server'.format(job.name, server.name))
                   for job in jobs for server in servers}

    # Allocation constraint
    for job in jobs:
        model.add(sum(allocations[(job, server)] for server in servers) <= 1)

    # Server resource speeds constraints
    for server in servers:
        model.add(sum(job.required_storage * allocations[(job, server)]
                      for job in jobs) <= server.storage_capacity)
        model.add(sum(job.compute_speed * allocations[(job, server)]
                      for job in jobs) <= server.computation_capacity)
        model.add(sum((job.loading_speed + job.sending_speed) * allocations[(job, server)]
                      for job in jobs) <= server.bandwidth_capacity)

    # Optimisation problem
    model.maximize(sum(job.value * allocations[(job, server)] for job in jobs for server in servers))

    # Solve the cplex model with time limit
    model_solution = model.solve(log_output=None, TimeLimit=time_limit)

    # Check that the model is solved
    if model_solution.get_solve_status() != SOLVE_STATUS_FEASIBLE and \
            model_solution.get_solve_status() != SOLVE_STATUS_OPTIMAL:
        print("Fixed VCG model failure")
        print_model_solution(model_solution)
        return None

    # Allocate all of the jobs to the servers
    try:
        for job in jobs:
            for server in servers:
                if model_solution.get_value(allocations[(job, server)]):
                    allocate(job, 0, 0, 0, server)
    except (KeyError, AssertionError) as e:
        print("Assertion error in fixed optimal algo: ", e)
        print_model_solution(model_solution)
        return None

    # Return the sum of the job value for all of teh running jobs
    return Result("Fixed Optimal", jobs, servers, round(model_solution.get_solve_time(), 2),
                  solve_status=model_solution.get_solve_status())
