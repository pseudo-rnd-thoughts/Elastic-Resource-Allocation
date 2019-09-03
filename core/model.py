"""This creates the models for the jobs and servers"""

from __future__ import annotations
from random import gauss, random
from typing import List, Tuple

from core.job import Job
from core.server import Server


def gaussian_dist(mean, std) -> int:
    """
    Uses gaussian distribution to generate a random number greater than 0 for a resource
    :param mean: Gaussian mean
    :param std: Gaussian standard deviation
    :return: A float of random gaussian distribution
    """
    return max(1, int(gauss(mean, std)))


class JobDist(object):
    """
    Random job distribution using gaussian (normal distribution)
    """

    def __init__(self, dist_name, probability,
                 storage_mean, storage_std,
                 computation_mean, computation_std,
                 results_data_mean, results_data_std,
                 value_mean, value_std,
                 deadline_mean, deadline_std):
        self.dist_name = dist_name
        self.probability = probability
        self.storage_mean = storage_mean
        self.storage_std = storage_std
        self.computation_mean = computation_mean
        self.computation_std = computation_std
        self.results_data_mean = results_data_mean
        self.results_data_std = results_data_std
        self.value_mean = value_mean
        self.value_std = value_std
        self.deadline_mean = deadline_mean
        self.deadline_std = deadline_std

    def create_job(self, name) -> Job:
        """
        Creates a new job with name (unique identifier)
        :param name: The name of the job
        :return: A new job object
        """
        job_name = "{} {}".format(self.dist_name, name)
        return Job(name=job_name,
                   required_storage=gaussian_dist(self.storage_mean, self.storage_std),
                   required_computation=gaussian_dist(self.computation_mean, self.computation_std),
                   required_results_data=gaussian_dist(self.results_data_mean, self.results_data_std),
                   value=gaussian_dist(self.value_mean, self.value_std),
                   deadline=int(gaussian_dist(self.deadline_mean, self.deadline_std)))


class ServerDist(object):
    """
    Random server distribution using gaussian (normal distribution)
    """

    def __init__(self, dist_name, probability,
                 storage_mean, storage_std,
                 computation_mean, computation_std,
                 results_data_mean, results_data_std):
        self.dist_name = dist_name
        self.probability = probability
        self.storage_mean = storage_mean
        self.storage_std = storage_std
        self.computation_mean = computation_mean
        self.computation_std = computation_std
        self.results_data_mean = results_data_mean
        self.results_data_std = results_data_std

    def create_server(self, name) -> Server:
        """
        Creates a new server with name (unique identifier)
        :param name: The name of the server
        :return: A new job object
        """
        server_name = "{} {}".format(self.dist_name, name)
        return Server(name=server_name,
                      max_storage=gaussian_dist(self.storage_mean, self.storage_std),
                      max_computation=gaussian_dist(self.computation_mean, self.computation_std),
                      max_bandwidth=gaussian_dist(self.results_data_mean, self.results_data_std))


class ModelDist(object):
    """Model distributions"""
    num_jobs = 0
    num_servers = 0

    def __init__(self, dist_name: str, job_dists: List[JobDist], num_jobs: int,
                 server_dists: List[ServerDist], num_servers: int):
        self.file_name = "{}_j{}_s{}".format(dist_name, num_jobs, num_servers)
        self.dist_name = dist_name

        self.job_dists = job_dists
        self.num_jobs = num_jobs
        self.server_dists = server_dists
        self.num_servers = num_servers

    def create(self) -> Tuple[List[Job], List[Server]]:
        """
        Creates a list of jobs and servers from a job and server distribution
        :return: A list of jobs and list of servers
        """
        jobs: List[Job] = []
        for job_pos in range(self.num_jobs):
            prob = random()
            for job_dist in self.job_dists:
                if prob < job_dist.probability:
                    jobs.append(job_dist.create_job(job_pos))
                    break
                else:
                    prob -= job_dist.probability

        servers: List[Server] = []
        for server_pos in range(self.num_servers):
            prob = random()
            for server_dist in self.server_dists:
                if prob < server_dist.probability:
                    servers.append(server_dist.create_server(server_pos))
                    break
                else:
                    prob -= server_dist.probability

        return jobs, servers


def load_dist(file_name: str) -> Tuple[str, List[JobDist], List[ServerDist]]:
    """
    Loads jobs and server distributions from a file
    :param file_name: The file to load from
    :return: A tuple of the list of random job distributions and random server distributions
    """

    job_dists: List[JobDist] = []
    server_dists: List[ServerDist] = []
    with open(file_name) as f:
        lines = f.readlines()
        name, num_job_dists, _ = lines[0].split(" ")

        for pos, line in enumerate(lines[1:int(num_job_dists) + 1]):
            job_name, probability, \
                storage_mean, storage_std,\
                computation_mean, computation_std,\
                results_data_mean, results_data_std, \
                utility_mean, utility_std,\
                deadline_mean, deadline_std = line.split(" ")
            job_dists.append(JobDist(job_name, float(probability),
                                     float(storage_mean), float(storage_std),
                                     float(computation_mean), float(computation_std),
                                     float(results_data_mean), float(results_data_std),
                                     float(utility_mean), float(utility_std),
                                     float(deadline_mean), float(deadline_std)))

        for pos, line in enumerate(lines[int(num_job_dists) + 1:]):
            server_name, probability, \
                storage_mean, storage_std, \
                computation_mean, computation_std, \
                results_data_mean, results_data_std = line.split(" ")
            server_dists.append(ServerDist(server_name, float(probability),
                                           float(storage_mean), float(storage_std),
                                           float(computation_mean), float(computation_std),
                                           float(results_data_mean), float(results_data_std)))

        return name, job_dists, server_dists


def reset_model(jobs: List[Job], servers: List[Server]):
    """
    Resets all of the jobs and servers back after an allocation
    :param jobs: A list of jobs
    :param servers: A list of servers
    """
    for job in jobs:
        job.reset_allocation()

    for server in servers:
        server.reset_allocations()
