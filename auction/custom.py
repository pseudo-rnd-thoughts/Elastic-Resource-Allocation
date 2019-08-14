"""Custom auction by Mark and Seb"""

from __future__ import annotations
from typing import List, Tuple, Dict

from core.job import Job
from core.server import Server

from docplex.cp.model import CpoModel


def evaluate_job_price(new_job: Job, server: Server, epsilon=1):
    model = CpoModel("Job Price")

    loading_speed = {job: model.integer_var(min=1, name="Job {} loading speed".format(job.name))
                     for job in server.allocated_jobs + [new_job]}
    compute_speed = {job: model.integer_var(min=1, name="Job {} compute speed".format(job.name))
                     for job in server.allocated_jobs + [new_job]}
    sending_speed = {job: model.integer_var(min=1, name="Job {} sending speed".format(job.name))
                     for job in server.allocated_jobs + [new_job]}
    allocated = {job: model.binary_var(name="Job {} allocated".format(job.name)) for job in server.allocated_jobs}

    for job in server.allocated_jobs + [new_job]:
            model.add(job.required_storage / loading_speed[job] +
                      job.required_computation / compute_speed[job] +
                      job.required_results_data / sending_speed[job] <= job.deadline)

    model.add(sum(job.required_storage * allocated[job] for job in server.allocated_jobs) +
              new_job.required_storage <= server.max_storage)
    model.add(sum(compute_speed[job] * allocated[job] for job in server.allocated_jobs) +
              compute_speed[new_job] <= server.max_computation)
    model.add(sum((loading_speed[job] + sending_speed[job]) * allocated[job] for job in server.allocated_jobs) +
              (loading_speed[new_job] + sending_speed[new_job]) <= server.max_bandwidth)

    model.maximize(sum(job.price * allocated[job] for job in server.allocated_jobs))

    model_solution = model.solve()
    job_price = server.total_price - model_solution.get_objective_values() + epsilon
    loading = {job: model_solution.get_value(loading_speed[job]) for job in server.allocated_jobs + [new_job]}
    compute = {job: model_solution.get_value(compute_speed[job]) for job in server.allocated_jobs + [new_job]}
    sending = {job: model_solution.get_value(sending_speed[job]) for job in server.allocated_jobs + [new_job]}
    allocation = {job: model_solution.get_value(allocated[job]) for job in server.allocated_jobs}
    return job_price, loading, compute, sending, allocation, server


def allocate_jobs(job_price: float, new_job: Job, server: Server,
                  loading: Dict[Job, int], compute: Dict[Job, int], sending: Dict[Job, int],
                  allocation: Dict[Job, bool], unallocated_jobs: List[Job]):
    """

    :param job_price:
    :param new_job:
    :param server:
    :param loading:
    :param compute:
    :param sending:
    :param allocation:
    :param unallocated_jobs:
    :return:
    """
    server.reset_allocations()

    new_job.price = job_price
    new_job.allocate(loading[new_job], compute[new_job], sending[new_job], server, price=job_price)
    server.allocate_job(loading[new_job], compute[new_job], sending[new_job], job)

    for job in server.allocated_jobs:
        if allocation[job]:
            job.allocate(loading[job], compute[job], sending[job], server)
            server.allocate_job(loading[job], compute[job], sending[job], job)
        else:
            job.reset_allocation()
            unallocated_jobs.append(job)


def custom_auction(jobs: List[Job], servers: List[Server]):
    """

    :param jobs:
    :param servers:
    :return:
    """
    unallocated_jobs = jobs.copy()
    while len(unallocated_jobs):
        job = unallocated_jobs[0]

        job_price, loading, compute, sending, allocation, \
            server = min((evaluate_job_price(job, server) for server in servers), key=lambda bid: bid[0])
        if job_price <= job.utility:
            print("Adding job {} to server {} with price {}".format(job.name, server.name, job_price))
            allocate_jobs(job_price, job, server, loading, compute, sending, allocation, unallocated_jobs)
        else:
            print("Removing Job {} from the unallocated job as the min price is {} and job utility is {}"
                  .format(job.name, job_price, job.utility))
            unallocated_jobs.remove(job)
