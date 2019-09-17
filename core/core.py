"""Additional functions"""

from __future__ import annotations

from typing import Iterable, Dict, Union, List, Tuple, TypeVar
from random import choice
import sys

from core.model import ModelDist
from core.job import Job
from core.server import Server

T = TypeVar('T')


def rand_list_max(args: Iterable[T], key=None) -> T:
    """
    Finds the maximum value in a list of values, if multiple values are all equal then choice a random value
    :param args: A list of values
    :param key: The key value function
    :return: A random maximum value
    """
    solution = []
    value = None

    for arg in args:
        arg_value = arg if key is None else key(arg)

        if arg_value is None or arg_value > value:
            solution = [arg]
            value = arg_value
        elif arg_value == value:
            solution = [arg]

    return choice(solution)


def load_args() -> Dict[str, Union[str, int]]:
    """
    Gets all of the arguments and places in a dictionary
    :return: All of the arguments in a dictionary
    """
    return {
        'model': 'models/'+sys.argv[1],
        'jobs': sys.argv[2],
        'servers': sys.argv[3],
        'repeat': sys.argv[4]
    }


def save_filename(test_name: str, model_dist: ModelDist, repeat: int = None) -> str:
    """
    Generates the save filename based on the info
    :param test_name: The test name
    :param model_dist: The model distribution
    :param repeat: The repeat number
    :return: The save filename
    """
    if repeat is None:
        return '{}_{}.json'.format(test_name, model_dist)
    else:
        return '{}_{}_{}.json'.format(test_name, model_dist, repeat)


def print_job_values(job_values: List[Tuple[Job, float]]):
    """
    Print the job utility values
    :param job_values: A list of tuples with the job and its value
    """
    print("\t\tJobs")
    max_job_id_len = max(len(job.name) for job, value in job_values) + 1
    print("{:<{id_len}}| Value | Storage | Compute | models | Value | Deadline ".format("Id", id_len=max_job_id_len))
    for job, value in job_values:
        # noinspection PyStringFormat
        print("{:<{id_len}}|{:^7.3f}|{:^9}|{:^9}|{:^8}|{:^9.3f}|{:^10}"
              .format(job.name, value, job.required_storage, job.required_computation,
                      job.required_results_data, job.value, job.deadline, id_len=max_job_id_len))
    print()


def print_job_allocation(job: Job, allocated_server: Server, s: int, w: int, r: int):
    """
    Prints the job allocation resource speeds
    :param job: The job
    :param allocated_server: The server
    :param s: The loading speed
    :param w: The compute speed
    :param r: The sending speed
    """
    print("Job {} - Server {}, loading speed: {}, compute speed: {}, sending speed: {}"
          .format(job.name, allocated_server.name, s, w, r))


def allocate(job: Job, loading: int, compute: int, sending: int, server: Server, price: float = None):
    """
    Allocate a job to a server
    :param job: The job
    :param loading: The loading speed
    :param compute: The compute speed
    :param sending: The sending speed
    :param server: The server
    :param price: The price
    """
    job.allocate(loading, compute, sending, server, price)
    server.allocate_job(job)
