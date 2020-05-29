"""Additional functions"""

from __future__ import annotations

import pickle
import re
import sys
from enum import Enum, auto
from random import choice, getstate as random_state
from typing import Iterable, Dict, Union, List, Tuple, TypeVar

import matplotlib.pyplot as plt
from docplex.cp.solution import CpoSolveResult

from src.core.job import Job
from src.core.model import ModelDist
from src.core.server import Server

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
    assert len(sys.argv) == 5, "Args: {}".format(sys.argv)
    assert sys.argv[2].isdigit(), "Jobs: {}".format(sys.argv[2])
    assert sys.argv[3].isdigit(), "Servers: {}".format(sys.argv[3])
    assert sys.argv[4].isdigit(), "Repeat: {}".format(sys.argv[4])

    return {
        'model': 'models/' + sys.argv[1] + '.json',
        'jobs': int(sys.argv[2]),
        'servers': int(sys.argv[3]),
        'repeat': int(sys.argv[4])
    }


def results_filename(test_name: str, model_dist: ModelDist, repeat: int = None) -> str:
    """
    Generates the save filename for testing results
    :param test_name: The test name
    :param model_dist: The model distribution
    :param repeat: The repeat number
    :return: The concatenation of the test name, model distribution name and the repeat
    """
    if repeat is None:
        return '{}_{}.json'.format(test_name, model_dist)
    else:
        return '{}_{}_{}.json'.format(test_name, model_dist, repeat)


def analysis_filename(test_name: str, axis: str) -> str:
    """
    Generates the save filename for Analysis plot results
    :param test_name: The test name
    :param axis: The axis name
    :return: The concatenation of the test name and the axis
    """
    return '{}_{}'.format(test_name, axis.lower().replace(" ", "_"))


def print_job_values(job_values: List[Tuple[Job, float]]):
    """
    Print the job utility values
    :param job_values: A list of tuples with the job and its value
    """
    print("\t\tJobs")
    max_job_name_len = max(len(job.name) for job, value in job_values) + 1
    print("{:<{name_len}}| Value | Storage | Compute | models | Value | Deadline "
          .format("Id", name_len=max_job_name_len))
    for job, value in job_values:
        # noinspection PyStringFormat
        print("{:<{name_len}}|{:^7.3f}|{:^9}|{:^9}|{:^8}|{:^7.1f}|{:^8}"
              .format(job.name, value, job.required_storage, job.required_computation,
                      job.required_results_data, job.value, job.deadline, name_len=max_job_name_len))
    print()


def print_job_allocation(jobs: List[Job]):
    """
    Prints the job allocation resource speeds
    :param jobs: List of jobs
    """
    print("Job Allocation")
    max_job_name_len = max(len(job.name) for job in jobs) + 1
    for job in jobs:
        if job.running_server:
            print("Job {:<{name_len}} - Server {}, loading: {}, compute: {}, sending: {}"
                  .format(job.name, job.running_server.name, job.loading_speed, job.compute_speed, job.sending_speed,
                          name_len=max_job_name_len))
        else:
            print("Job {} - None".format(job.name))


def allocate(job: Job, loading: int, compute: int, sending: int, server: Server, price: float = 0):
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


def list_item_replacement(lists: List[T], old_item: T, new_item: T):
    """
    Replace the item in the list
    :param lists: The list
    :param old_item: The item to remove
    :param new_item: The item to append
    """
    lists.remove(old_item)
    lists.append(new_item)


def list_copy_remove(lists: List[T], item: T) -> List[T]:
    """
    Copy the list and remove an item
    :param lists: The list
    :param item: The item to remove
    :return: The copied list without the item
    """
    list_copy = lists.copy()
    list_copy.remove(item)
    return list_copy


def save_random_state(filename):
    """
    Save the random state to the filename
    :param filename: The filename to save the state to
    """
    with open(filename, 'w') as file:
        pickle.dumps(file, random_state())


def print_model_solution(model_solution: CpoSolveResult):
    """
    Print the model solution information
    :param model_solution: The model solution
    """
    print("Solve status: {}, Fail status: {}".format(model_solution.get_solve_status(),
                                                     model_solution.get_fail_status()))
    print("Search status: {}, Stop Cause: {}, Solve Time: {} secs".format(model_solution.get_search_status(),
                                                                          model_solution.get_stop_cause(),
                                                                          round(model_solution.get_solve_time(), 2)))


def print_model(jobs: List[Job], servers: List[Server]):
    """
    Print the model
    :param jobs: The list of jobs
    :param servers: The list of servers
    """
    print("Job Name | Storage | Computation | Results Data | Value | Loading | Compute | Sending | Deadline | Price")
    for job in jobs:
        print("{:^9s}|{:^9d}|{:^13d}|{:^14d}|{:^7.1f}|{:^9d}|{:^9d}|{:^9d}|{:^10d}| {:.2f}"
              .format(job.name, job.required_storage, job.required_computation, job.required_results_data, job.value,
                      job.loading_speed, job.compute_speed, job.sending_speed, job.deadline, job.price))

    print("\nServer Name | Storage | Computation | Bandwidth | Allocated Jobs")
    for server in servers:
        print("{:^12s}|{:^9d}|{:^13d}|{:^11d}| {}".format(server.name, server.storage_capacity,
                                                          server.computation_capacity,
                                                          server.bandwidth_capacity,
                                                          ', '.join([job.name for job in server.allocated_jobs])))


# noinspection LongLine
def decode_filename(folder: str, encoded_file: str) -> Tuple[str, str, str]:
    """
    Decodes the filename to recover the file location, the model name and the greedy name
    :param folder: The data folder
    :param encoded_file: The encoded filename
    :return: Tuple of the location of the file and the model type
    """
    return "../results/{}/{}.json".format(folder, encoded_file), \
           re.findall(r"j\d+_s\d+", encoded_file)[0].replace("_", " ").replace("s", "Servers: ").replace("j", "Jobs: "), \
           encoded_file.replace(re.findall(r"_j\d+_s\d+_0", encoded_file)[0], "")


class ImageFormat(Enum):
    """
    Image format
    """
    EPS = auto()
    PNG = auto()
    PDF = auto()
    BOTH = auto()
    NONE = auto()


def save_plot(name: str, test_folder: str, additional: str = "",
              image_format: ImageFormat = ImageFormat.NONE, lgd=None):
    """
    Saves the plot to a file of the particular image format
    :param name: The plot name
    :param test_folder: The test name
    :param additional: Additional information to add to the filename
    :param image_format: The image format
    :param lgd: The legend to be added to the plot when saved
    """
    if lgd:
        lgd = (lgd,)
    if image_format == ImageFormat.EPS:
        filename = f'{test_folder}/eps/{name}{additional}.eps'
        print("Save file location: " + filename)
        plt.savefig(filename, format='eps', dpi=1000, bbox_extra_artists=lgd, bbox_inches='tight')
    elif image_format == ImageFormat.PNG:
        filename = f'{test_folder}/png/{name}{additional}.png'
        print("Save file location: " + filename)
        plt.savefig(filename, format='png', bbox_extra_artists=lgd, bbox_inches='tight')
    elif image_format == ImageFormat.BOTH:
        save_plot(name, test_folder, additional, ImageFormat.EPS, lgd)
        save_plot(name, test_folder, additional, ImageFormat.PNG, lgd)
    elif image_format == ImageFormat.PDF:
        filename = f'{test_folder}/eps/{name}{additional}.pdf'
        print("Save file location: " + filename)
        plt.savefig(filename, format='pdf')
