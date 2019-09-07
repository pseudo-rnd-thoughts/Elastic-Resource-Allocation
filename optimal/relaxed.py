"""Relaxed model with a single super server allow a upper bound to be found, solved through mixed integer programming"""

from __future__ import annotations

from typing import List, Dict, Tuple, Optional

from docplex.cp.config import context
from docplex.cp.model import CpoModel, CpoVariable
from docplex.cp.solution import CpoSolveResult
from docplex.cp.solution import SOLVE_STATUS_UNKNOWN

from core.job import Job
from core.result import Result
from core.server import Server

context.log_output = None


def generate_model(jobs: List[Job], servers: List[Server]) -> Tuple[CpoModel, Dict[Job, CpoVariable],
                                                                   Dict[Job, CpoVariable], Dict[Job, CpoVariable],
                                                                   Dict[Job, CpoVariable], Server]:
    """
    Generates a model for the algorithm
    :param jobs: The list of jobs
    :param servers: The list of servers
    :return: The generated model and the variables
    """
    model = CpoModel("Server Job Allocation")

    loading_speeds: Dict[Job, CpoVariable] = {}
    compute_speeds: Dict[Job, CpoVariable] = {}
    sending_speeds: Dict[Job, CpoVariable] = {}
    job_allocation: Dict[Job, CpoVariable] = {}

    super_server = Server('Super Server',
                          sum(server.max_storage for server in servers),
                          sum(server.max_computation for server in servers),
                          sum(server.max_bandwidth for server in servers))

    for job in jobs:
        loading_speeds[job] = model.integer_var(min=1, max=super_server.max_bandwidth,
                                                name="{} loading speed".format(job.name))
        compute_speeds[job] = model.integer_var(min=1, max=super_server.max_computation,
                                                name="{} compute speed".format(job.name))
        sending_speeds[job] = model.integer_var(min=1, max=super_server.max_bandwidth,
                                                name="{} sending speed".format(job.name))
        job_allocation[job] = model.binary_var(name="{} allocation".format(job.name))

        model.add(job.required_storage / loading_speeds[job] +
                  job.required_computation / compute_speeds[job] +
                  job.required_results_data / sending_speeds[job] <= job.deadline)

    model.add(sum(job.required_storage * job_allocation[job]
                  for job in jobs) <= super_server.max_storage)
    model.add(sum(compute_speeds[job] * job_allocation[job]
                  for job in jobs) <= super_server.max_computation)
    model.add(sum((loading_speeds[job] + sending_speeds[job]) * job_allocation[job]
                  for job in jobs) <= super_server.max_bandwidth)

    model.maximize(sum(job.value * job_allocation[job] for job in jobs))

    return model, loading_speeds, compute_speeds, sending_speeds, job_allocation, super_server


def run_cplex_model(model: CpoModel, jobs: List[Job], super_server: Server, loading_speeds: Dict[Job, CpoVariable],
                    compute_speeds: Dict[Job, CpoVariable], sending_speeds: Dict[Job, CpoVariable],
                    job_allocation: Dict[Job, CpoVariable],
                    time_limit: int = 500, debug_time: bool = True) -> Optional[Result]:
    """
    Runs the cplex model
    :param model: The model to run
    :param jobs: A list of jobs
    :param super_server: A super server
    :param loading_speeds: A dictionary of the loading speeds
    :param compute_speeds: A dictionary of the compute speeds
    :param sending_speeds: A dictionary of the sending speeds
    :param job_allocation: A dictionary of the servers and jobs to binary variable
    :param time_limit: The time limit
    :param debug_time: Print the time taken
    :return: A results
    """

    model_solution: CpoSolveResult = model.solve(log_output=None, RelativeOptimalityTolerance=0.01,
                                                 TimeLimit=time_limit)
    if debug_time:
        print("Solve time: {} secs, Objective value: {}, bounds: {}, gaps: {}"
              .format(round(model_solution.get_solve_time(), 2), model_solution.get_objective_values(),
                      model_solution.get_objective_bounds(), model_solution.get_objective_gaps()))

    if model_solution.get_solve_status() == SOLVE_STATUS_UNKNOWN:
        return None

    for job in jobs:
        if model_solution.get_value(job_allocation[job]):
            s = model_solution.get_value(loading_speeds[job])
            w = model_solution.get_value(compute_speeds[job])
            r = model_solution.get_value(sending_speeds[job])
            job.allocate(s, w, r, super_server)
            super_server.allocate_job(job)

    return Result("Relaxed", jobs, [super_server])


def relaxed_algorithm(jobs: List[Job], servers: List[Server],
                      time_limit: int = 500, debug_time: bool = False) -> Result:
    """
    Runs the optimal algorithm solution
    :param jobs: A list of jobs
    :param servers: A list of servers
    :param time_limit: The time limit to solve
    :param debug_time: If to print the time taken
    :return: The result from optimal solution
    """

    model, loading_speeds, compute_speeds, sending_speed, job_allocation, super_server = generate_model(jobs, servers)

    return run_cplex_model(model, jobs, super_server, loading_speeds, compute_speeds, sending_speed, job_allocation,
                           time_limit, debug_time)