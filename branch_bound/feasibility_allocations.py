from typing import Dict, List, Tuple, Optional

from docplex.cp.model import CpoModel, CpoVariable
from docplex.cp.solution import SOLVE_STATUS_FEASIBLE

from core.fixed_job import FixedJob
from core.job import Job
from core.server import Server


def flexible_feasible_allocation(job_server_allocations: Dict[Server, List[Job]],
                                 time_limit: int = 60) -> Optional[Dict[Job, Tuple[int, int, int]]]:
    """
    Checks whether a job to server allocation is a feasible solution to the problem
    :param job_server_allocations: The current job allocation
    :param time_limit: The time limit to solve the problem within
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

    model_solution = model.solve(log_output=None, TimeLimit=time_limit)
    if model_solution.get_solve_status() == SOLVE_STATUS_FEASIBLE:
        return {job: (model_solution.get_value(loading_speeds[job]),
                      model_solution.get_value(compute_speeds[job]),
                      model_solution.get_value(sending_speeds[job]))
                for jobs in job_server_allocations.values() for job in jobs}
    else:
        return None


def fixed_feasible_allocation(job_server_allocations: Dict[Server, List[FixedJob]],
                              time_limit: int = 60) -> Optional[Dict[FixedJob, Tuple[int, int, int]]]:
    """
    Checks whether a job to server allocation is a feasible solution to the problem
    :param job_server_allocations: The current job allocation
    :param time_limit: The time limit to solve the problem within
    :return: An optional dictionary of the job to the tuple of resource speeds
    """
    model = CpoModel("Allocation Feasibility")

    for server, jobs in job_server_allocations.items():
        for job in jobs:
            model.add((job.required_storage / job.loading_speed) +
                      (job.required_computation / job.compute_speed) +
                      (job.required_results_data / job.sending_speed) <= job.deadline)

        model.add(sum(job.required_storage for job in jobs) <= server.storage_capacity)
        model.add(sum(job.compute_speed for job in jobs) <= server.computation_capacity)
        model.add(sum((job.loading_speed + job.sending_speed) for job in jobs) <= server.bandwidth_capacity)

    model_solution = model.solve(log_output=None, TimeLimit=time_limit)
    if model_solution.get_solve_status() == SOLVE_STATUS_FEASIBLE:
        return {job: (job.loading_speed, job.compute_speed, job.sending_speed)
                for jobs in job_server_allocations.values() for job in jobs}
    else:
        return None
