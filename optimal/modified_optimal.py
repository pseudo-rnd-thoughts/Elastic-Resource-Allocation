"""Implementation of the problem using cplex mp"""

from typing import List

from docplex.mp.model import Model
from docplex.cp.model import CpoModel

from core.job import Job
from core.server import Server
from core.model import load_dist, ModelDist


def optimal_mp_algorithm(jobs: List[Job], servers: List[Server]):
    """
    An implementation of cplex mp with the current problem case
    !!! THIS ALGORITHM WOULDNT WORK !!!
    :param jobs: A list of jobs
    :param servers: A list of servers
    """
    model: Model = Model("Optimal")

    loading_speeds, compute_speeds, sending_speeds, server_job_allocation = {}, {}, {}, {}
    for job in jobs:
        loading_speeds[job] = model.continuous_var(lb=0, name="Job {} loading speed".format(job.name))
        compute_speeds[job] = model.continuous_var(lb=0, name="Job {} compute speed".format(job.name))
        sending_speeds[job] = model.continuous_var(lb=0, name="Job {} sending speed".format(job.name))

        # This will fail as it doesnt let variable to be denominator (also lower bound of zero causes problems)
        # model.add(job.required_storage / loading_speeds[job] +
        #           job.required_computation / compute_speeds[job] +
        #           job.required_results_data / sending_speeds[job] <= job.deadline)
        # This will fail as it doesnt allow more than 2 variable multiplied together (the deadline part is not allowed)
        model.add(job.required_storage * compute_speeds[job] * sending_speeds[job] +
                  loading_speeds[job] * job.required_computation * sending_speeds[job] +
                  loading_speeds[job] * compute_speeds[job] * job.required_results_data <=
                  job.deadline * loading_speeds[job] * compute_speeds[job] * sending_speeds[job])

        for server in servers:
            server_job_allocation[(server, job)] = model.binary_var(name="Job {} allocation to server {}"
                                                                    .format(job.name, server.name))

        model.add(sum(server_job_allocation[(server, job)] for server in servers) <= 1)

    for server in servers:
        model.add(sum(job.required_storage * server_job_allocation[(server, job)]
                      for job in jobs) <= server.max_storage)
        model.add(sum(compute_speeds[job] * server_job_allocation[(server, job)]
                      for job in jobs) <= server.max_computation)
        model.add(sum((loading_speeds[job] + sending_speeds[job]) * server_job_allocation[(server, job)]
                      for job in jobs) <= server.max_bandwidth)

    model.maximize(sum(job.utility * server_job_allocation[(server, job)] for job in jobs for server in servers))

    model.print_information()
    model.solve()


def modified_mp_optimal_algorithm(jobs: List[Job], servers: List[Server]):
    """
    An implementation of the modified problem case where the loading and sending speed are a single variable
    :param jobs: A list of jobs
    :param servers: A list of servers
    """
    model = Model("Modified MP Optimal")

    communication_speeds, compute_speeds, server_job_allocation = {}, {}, {}
    max_communication_speed = max(server.max_bandwidth for server in servers)
    max_compute_speed = max(server.max_computation for server in servers)

    for job in jobs:
        communication_speeds[job] = model.continuous_var(lb=0, name="Job {} communication speed".format(job.name))
        compute_speeds[job] = model.continuous_var(lb=0, name="Job {} compute speed".format(job.name))

        # Same problem of variable are not allowed as denominator
        # model.add((job.required_storage + job.required_results_data) / communication_speeds[job] +
        #     job.required_computation / compute_speeds[job] <= job.deadline)
        model.add((job.required_storage + job.required_results_data) * compute_speeds[job] +
                  job.required_computation * communication_speeds[job] -
                  job.deadline * communication_speeds[job] * communication_speeds[job] <= 0)
        
        for server in servers:
            server_job_allocation[(server, job)] = model.binary_var(name="Job {} allocation to server {}"
                                                                    .format(job.name, server.name))
            
            model.add(communication_speeds[job] <= server_job_allocation[(server, job)] * max_communication_speed)
            model.add(compute_speeds[job] <= server_job_allocation[(server, job)] * max_compute_speed)
            
        model.add(sum(server_job_allocation[(server, job)] for server in servers) <= 1)
        
    for server in servers:
        model.add(sum(job.required_storage * server_job_allocation[(server, job)]
                      for job in jobs) <= server.max_storage)
        model.add(sum(compute_speeds[job] for job in jobs) <= server.max_computation)
        model.add(sum(communication_speeds[job] for job in jobs) <= server.max_bandwidth)

    model.maximize(sum(job.utility * server_job_allocation[(server, job)] for job in jobs for server in servers))
    
    model.print_information()
    model_solution = model.solve()
    return model_solution


def modified_cp_optimal_algorithm(jobs: List[Job], servers: List[Server]):
    """
    Modified CP optimal algorithm
    :param jobs: A list of jobs
    :param servers: A list of servers
    :return: The model solution
    """
    model = CpoModel("Modified CP Optimal")

    communication_speeds, compute_speeds, server_job_allocation = {}, {}, {}

    for job in jobs:
        communication_speeds[job] = model.integer_var(min=0, name="Job {} communication speed".format(job.name))
        compute_speeds[job] = model.integer_var(min=0, name="Job {} compute speed".format(job.name))

        # Same problem of variable are not allowed as denominator
        model.add((job.required_storage + job.required_results_data) / communication_speeds[job] +
                  job.required_computation / compute_speeds[job] <= job.deadline)
        model.add((job.required_storage + job.required_results_data) * compute_speeds[job] +
                  job.required_computation * communication_speeds[job] <=
                  job.deadline * communication_speeds[job] * communication_speeds[job])

        for server in servers:
            server_job_allocation[(server, job)] = model.binary_var(name="Job {} allocation to server {}"
                                                                    .format(job.name, server.name))

        model.add(sum(server_job_allocation[(server, job)] for server in servers) <= 1)

    for server in servers:
        model.add(sum(job.required_storage * server_job_allocation[(server, job)]
                      for job in jobs) <= server.max_storage)
        model.add(sum(compute_speeds[job] * server_job_allocation[(server, job)]
                      for job in jobs) <= server.max_computation)
        model.add(sum(communication_speeds[job] * server_job_allocation[(server, job)]
                      for job in jobs) <= server.max_bandwidth)

    model.maximize(sum(job.utility * server_job_allocation[(server, job)] for job in jobs for server in servers))

    model.print_information()
    model_solution = model.solve()

    return model_solution


if __name__ == "__main__":
    model_name, job_dist, server_dist = load_dist('../models/basic.model')
    model_dist = ModelDist(model_name, job_dist, 15, server_dist, 3)

    _jobs, _servers = model_dist.create()
    modified_mp_optimal_algorithm(_jobs, _servers)
