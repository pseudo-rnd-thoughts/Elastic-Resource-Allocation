"""Relaxed model with a single super server allow a upper bound to be found, solved through mixed integer programming"""

from __future__ import annotations

from time import time
from typing import List, Dict, Optional

from docplex.cp.model import CpoModel, CpoVariable
from docplex.cp.solution import CpoSolveResult
from docplex.cp.solution import SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL

from core.core import print_model, print_model_solution
from core.job import Job
from core.result import Result
from core.server import Server
from core.super_server import SuperServer


def relaxed_algorithm(jobs: List[Job], servers: List[Server], time_limit: int,
                      debug_time: bool = False) -> Optional[Result]:
    """
    Runs the optimal algorithm solution
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param time_limit: The time limit to solve
    :param debug_time: If to print the time taken
    :return: The result from optimal solution
    """
    start_time = time()

    model = CpoModel("Server Job Allocation")

    loading_speeds: Dict[Job, CpoVariable] = {}
    compute_speeds: Dict[Job, CpoVariable] = {}
    sending_speeds: Dict[Job, CpoVariable] = {}
    job_allocation: Dict[Job, CpoVariable] = {}

    super_server = SuperServer(servers)

    for job in jobs:
        loading_speeds[job] = model.integer_var(min=1, max=super_server.bandwidth_capacity,
                                                name="{} loading speed".format(job.name))
        compute_speeds[job] = model.integer_var(min=1, max=super_server.computation_capacity,
                                                name="{} compute speed".format(job.name))
        sending_speeds[job] = model.integer_var(min=1, max=super_server.bandwidth_capacity,
                                                name="{} sending speed".format(job.name))
        job_allocation[job] = model.binary_var(name="{} allocation".format(job.name))

        model.add(job.required_storage / loading_speeds[job] +
                  job.required_computation / compute_speeds[job] +
                  job.required_results_data / sending_speeds[job] <= job.deadline)

    model.add(sum(job.required_storage * job_allocation[job]
                  for job in jobs) <= super_server.storage_capacity)
    model.add(sum(compute_speeds[job] * job_allocation[job]
                  for job in jobs) <= super_server.computation_capacity)
    model.add(sum((loading_speeds[job] + sending_speeds[job]) * job_allocation[job]
                  for job in jobs) <= super_server.bandwidth_capacity)

    model.maximize(sum(job.value * job_allocation[job] for job in jobs))

    # Run the model
    model_solution: CpoSolveResult = model.solve(log_output=None, RelativeOptimalityTolerance=0.01,
                                                 TimeLimit=time_limit)
    if debug_time:
        print("Solve time: {} secs, Objective value: {}, bounds: {}, gaps: {}"
              .format(round(model_solution.get_solve_time(), 2), model_solution.get_objective_values(),
                      model_solution.get_objective_bounds(), model_solution.get_objective_gaps()))

    # Check that it is solved
    if model_solution.get_solve_status() != SOLVE_STATUS_FEASIBLE and \
            model_solution.get_solve_status() != SOLVE_STATUS_OPTIMAL:
        print("Optimal algorithm failed")
        print_model_solution(model_solution)
        print_model(jobs, servers)
        return None

    # For each of the jobs allocate if allocated to the server
    for job in jobs:
        if model_solution.get_value(job_allocation[job]):
            job.allocate(model_solution.get_value(loading_speeds[job]), model_solution.get_value(compute_speeds[job]),
                         model_solution.get_value(sending_speeds[job]), super_server)
            super_server.allocate_job(job)

    return Result("Relaxed", jobs, [super_server], time() - start_time, solve_status=model_solution.get_solve_status())
