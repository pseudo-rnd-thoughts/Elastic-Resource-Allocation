"""Optimal solution through mixed integer programming"""

from __future__ import annotations

from typing import List, Dict, Tuple, Optional

from docplex.cp.model import CpoModel, CpoVariable
from docplex.cp.solution import SOLVE_STATUS_UNKNOWN

from core.job import Job
from core.result import Result
from core.server import Server


def optimal_algorithm(jobs: List[Job], servers: List[Server], time_limit: int) -> Optional[Result]:
    """
    Runs the optimal algorithm solution
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param time_limit: The time limit to solve
    :return: The result from optimal solution
    """
    assert time_limit > 0, "Time limit: {}".format(time_limit)

    model = CpoModel("Server Job Allocation")

    # The resource speed variables and the allocation variables
    loading_speeds: Dict[Job, CpoVariable] = {}
    compute_speeds: Dict[Job, CpoVariable] = {}
    sending_speeds: Dict[Job, CpoVariable] = {}
    server_job_allocation: Dict[Tuple[Job, Server], CpoVariable] = {}

    # The maximum bandwidth and the computation that the speed can be
    max_bandwidth, max_computation = max(server.max_bandwidth for server in servers) - 1, \
        max(server.max_computation for server in servers)

    # Loop over each job to allocate the variables and add the deadline constraints
    for job in jobs:
        loading_speeds[job] = model.integer_var(min=1, max=max_bandwidth, name="{} loading speed".format(job.name))
        compute_speeds[job] = model.integer_var(min=1, max=max_computation, name="{} compute speed".format(job.name))
        sending_speeds[job] = model.integer_var(min=1, max=max_bandwidth, name="{} sending speed".format(job.name))

        model.add(job.required_storage / loading_speeds[job] +
                  job.required_computation / compute_speeds[job] +
                  job.required_results_data / sending_speeds[job] <= job.deadline)

        # The job allocation variables and add the allocation constraint
        for server in servers:
            server_job_allocation[(job, server)] = model.binary_var(name="Job {} Server {}"
                                                                    .format(job.name, server.name))
        model.add(sum(server_job_allocation[(job, server)] for server in servers) <= 1)

    # For each server, add the resource constraint
    for server in servers:
        model.add(sum(job.required_storage * server_job_allocation[(job, server)]
                      for job in jobs) <= server.max_storage)
        model.add(sum(compute_speeds[job] * server_job_allocation[(job, server)]
                      for job in jobs) <= server.max_computation)
        model.add(sum((loading_speeds[job] + sending_speeds[job]) * server_job_allocation[(job, server)]
                      for job in jobs) <= server.max_bandwidth)

    # The optimisation statement
    model.maximize(sum(job.value * server_job_allocation[(job, server)] for job in jobs for server in servers))

    # Solve the cplex model with time limit
    model_solution = model.solve(log_output=None, RelativeOptimalityTolerance=0.01, TimeLimit=time_limit)

    # Check that it is solved
    if model_solution.get_solve_status() == SOLVE_STATUS_UNKNOWN:
        print("Optimal algorithm failued")
        return None

    # Generate the allocation of the jobs and servers
    for job in jobs:
        for server in servers:
            if model_solution.get_value(server_job_allocation[(job, server)]):
                s = model_solution.get_value(loading_speeds[job])
                w = model_solution.get_value(compute_speeds[job])
                r = model_solution.get_value(sending_speeds[job])
                job.allocate(s, w, r, server)
                server.allocate_job(job)

    return Result("Optimal", jobs, servers, round(model_solution.get_solve_time(), 2),
                  solve_status=model_solution.get_solve_status())
