"""Debugs the critical value auction"""

from __future__ import annotations

from typing import List, Tuple
from math import floor

from core.core import load_args
from core.model import reset_model, ModelDist, load_dist
from core.job import Job
from core.server import Server
from greedy.server_selection_policy import SumResources
from greedy.value_density import ValueDensity, UtilityPerResources
from greedy.resource_allocation_policy import SumPercentage
from greedy.greedy import allocate_jobs
from auctions.critical_value_auction import calculate_critical_value, critical_value_auction, cv_auction


def print_job_density(jobs: List[Job], value_density: ValueDensity):
    max_name = max(len(job.name) for job in jobs) + 1
    print("{:^{}}| Value | Density".format("Job Name", max_name))
    for job in jobs:
        print("{:^{}}|{:^7}|{:^6.2}".format(job.name, max_name, job.value, value_density.evaluate(job)))
    print()


def print_job_ordering(jobs: List[Job]):
    print("Job ordering: [{}]".format(', '.join([job.name for job in jobs])))


def print_job_allocation(servers: List[Server]):
    max_name = max(len(server.name) for server in servers)
    print("{:^{}} | Jobs allocated".format("Server", max_name))
    for server in servers:
        print("{:^{}} | {}".format(server.name, max_name, ', '.join([job.name for job in server.allocated_jobs])))
    print()


def critical_linear(critical_job: Job, jobs: List[Job], servers: List[Server], value_density: ValueDensity,
                    server_selection_policy, resource_allocation_policy) -> Tuple[float, int]:
    # print("New Job: " + critical_job.name)
    ranked_jobs = sorted((job for job in jobs), key=lambda job: value_density.evaluate(job), reverse=True)
    for pos in range(ranked_jobs.index(critical_job) + 1, len(ranked_jobs)):
        ranked_jobs.remove(critical_job)
        ranked_jobs.insert(pos, critical_job)

        reset_model(ranked_jobs, servers)

        allocate_jobs(ranked_jobs, servers, server_selection_policy, resource_allocation_policy)

        if critical_job.running_server:
            # print("Job allocated to server " + job.running_server.name + " at position " + str(pos))
            pass
        else:
            # print("Job not allocated in position " + str(pos))
            if pos < len(ranked_jobs) - 1:
                density = value_density.evaluate(ranked_jobs[pos - 1])
                print("Linear: {}".format(ranked_jobs[pos - 1].name))
                # print("Job below ({}) has density {:.2f}".format(ranked_jobs[pos + 1].name, density))
                # print("The critical value is {:.2f} for {} with original value {}".format(
                #       value_density.inverse(critical_job, density), critical_job.name, critical_job.value))
                return value_density.inverse(critical_job, density), pos
            break
    return 0, -1


def critical_binary(critical_job: Job, jobs: List[Job], servers: List[Server], value_density: ValueDensity,
                    server_selection_policy, resource_allocation_policy) -> Tuple[float, int]:
    # print("New Job: " + critical_job.name)
    ranked_jobs = sorted((job for job in jobs), key=lambda job: value_density.evaluate(job), reverse=True)
    upper_bound = ranked_jobs.index(critical_job) + 1
    lower_bound = len(ranked_jobs)
    allocation = list(" " * len(ranked_jobs))
    while upper_bound < lower_bound:
        pos = floor((lower_bound + upper_bound) / 2)
        if upper_bound == pos or lower_bound == pos:
            break
        # print("Upper: {}, Lower: {}, Pos: {}".format(upper_bound, lower_bound, pos))
        ranked_jobs.remove(critical_job)
        ranked_jobs.insert(pos, critical_job)

        reset_model(ranked_jobs, servers)

        allocate_jobs(ranked_jobs, servers, server_selection_policy, resource_allocation_policy)

        if critical_job.running_server:
            upper_bound = pos
        else:
            lower_bound = pos
        allocation[pos] = "1" if critical_job.running_server else "0"
        print("{}, U: {}, L: {}".format(''.join(allocation), upper_bound, lower_bound))

    # print("Job not allocated in position " + str(pos))
    if upper_bound < len(ranked_jobs) - 1:
        density = value_density.evaluate(ranked_jobs[upper_bound])
        print("Binary: {}".format(ranked_jobs[upper_bound].name))

        # print("Job below ({}) has density {:.2f}".format(ranked_jobs[pos + 1].name, density))
        # print("The critical value is {:.2f} for {} with original value {}".format(
        #       value_density.inverse(critical_job, density), critical_job.name, critical_job.value))
        return value_density.inverse(critical_job, density), upper_bound
    return 0, -1


def critical_all(critical_job: Job, jobs: List[Job], servers: List[Server], value_density: ValueDensity,
                 server_selection_policy, resource_allocation_policy):
    ranked_jobs = sorted((job for job in jobs), key=lambda job: value_density.evaluate(job), reverse=True)
    allocated = ""
    for pos in range(len(jobs)):
        ranked_jobs.remove(critical_job)
        ranked_jobs.insert(pos, critical_job)

        reset_model(ranked_jobs, servers)

        allocate_jobs(ranked_jobs, servers, server_selection_policy, resource_allocation_policy)

        allocated += "1" if critical_job.running_server else "0"
    print("All: " + allocated)

    allocations = list(allocated).count("1")
    return allocations if allocations < len(jobs) - 1 else -1


def debug_critical_value(model_dist):
    jobs, servers = model_dist.create()
    print_job_ordering(jobs)

    value_density = UtilityPerResources()
    server_selection_policy = SumResources()
    resource_allocation_policy = SumPercentage()

    print_job_density(jobs, value_density)

    ranked_jobs = sorted((job for job in jobs), key=lambda job: value_density.evaluate(job), reverse=True)
    allocate_jobs(ranked_jobs, servers, server_selection_policy, resource_allocation_policy)

    print_job_allocation(servers)

    allocation = {job: (job.loading_speed, job.compute_speed, job.sending_speed, job.running_server)
                  for job in ranked_jobs if job.running_server}

    print_job_ordering(ranked_jobs)
    for job in allocation.keys():
        print("Job: {}".format(job.name))
        linear_value, linear_pos = critical_linear(job, jobs, servers, value_density, server_selection_policy,
                                                   resource_allocation_policy)
        binary_value, binary_pos = critical_binary(job, jobs, servers, value_density, server_selection_policy,
                                                   resource_allocation_policy)
        optimal = critical_all(job, jobs, servers, value_density, server_selection_policy, resource_allocation_policy)
        critical = calculate_critical_value(job, jobs, servers, value_density, server_selection_policy,
                                            resource_allocation_policy)
        print(
            "Linear: {:.2f} ({}), Binary: {:.2f} ({}), Optimal: {}, Critical: {:.2f}\n".format(linear_value, linear_pos,
                                                                                               binary_value, binary_pos,
                                                                                               optimal, critical))


def debug_new_critical(model_dist: ModelDist):
    jobs, servers = model_dist.create()

    value_density = UtilityPerResources()
    server_selection_policy = SumResources()
    resource_allocation_policy = SumPercentage()

    critical_result = critical_value_auction(jobs, servers, value_density, server_selection_policy, resource_allocation_policy)
    for job in jobs:
        print("Job {} -> {}".format(job.name, job.price))

    reset_model(jobs, servers)
    new_critical_result = cv_auction(jobs, servers, value_density, server_selection_policy, resource_allocation_policy)
    for job in jobs:
        print("Job {} -> {}".format(job.name, job.price))


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    # debug_critical_value(loaded_model_dist)
    debug_new_critical(loaded_model_dist)
