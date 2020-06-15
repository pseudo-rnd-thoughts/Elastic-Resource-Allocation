"""Additional functions"""

from __future__ import annotations

import pickle
import re
import sys
from enum import Enum, auto
from random import choice, getstate as random_state, gauss
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from docplex.cp.solution import CpoSolveResult

if TYPE_CHECKING:
    from typing import Iterable, Dict, Union, List, Tuple, TypeVar

    from core.server import Server
    from core.task import Task

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
    assert len(sys.argv) == 5, f"Args: {sys.argv}"
    assert sys.argv[2].isdigit(), f"Jobs: {sys.argv[2]}"
    assert sys.argv[3].isdigit(), f"Servers: {sys.argv[3]}"
    assert sys.argv[4].isdigit(), f"Repeat: {sys.argv[4]}"

    return {
        'model': f'models/{sys.argv[1]}.json',
        'tasks': int(sys.argv[2]),
        'servers': int(sys.argv[3]),
        'repeat': int(sys.argv[4])
    }


def analysis_filename(test_name: str, axis: str) -> str:
    """
    Generates the save filename for Analysis plot results

    :param test_name: The test name
    :param axis: The axis name
    :return: The concatenation of the test name and the axis
    """
    if test_name == "":
        return axis.lower().replace(" ", "_")
    else:
        return f'{test_name}_{axis.lower().replace(" ", "_")}'


def print_task_values(task_values: List[Tuple[Task, float]]):
    """
    Print the task utility values

    :param task_values: A list of tuples with the task and its value
    """
    print('\t\tJobs')
    max_task_name_len = max(len(task.name) for task, value in task_values) + 1
    print(f"{'Id':<{max_task_name_len}}| Value | Storage | Compute | models | Value | Deadline ")
    for task, value in task_values:
        # noinspection PyStringFormat
        print(f'{task.name:<{max_task_name_len}}|{value:^7.3f}|{task.required_storage:^9}|{task.required_computation:^9}|'
              f'{task.required_results_data:^8}|{task.value:^7.1f}|{task.deadline:^8}')
    print()


def print_task_allocation(tasks: List[Task]):
    """
    Prints the task allocation resource speeds

    :param tasks: List of tasks
    """
    print('Job Allocation')
    max_task_name_len = max(len(task.name) for task in tasks) + 1
    for task in tasks:
        if task.running_server:
            print(f"Job {task.name:<{max_task_name_len}} - Server {task.running_server.name}, loading: {task.loading_speed},"
                  f" compute: {task.compute_speed}, sending: {task.sending_speed}")
        else:
            print(f'Job {task.name} - None')


def allocate(task: Task, loading: int, compute: int, sending: int, server: Server, price: float = None):
    """
    Allocate a task to a server

    :param task: The task
    :param loading: The loading speed
    :param compute: The compute speed
    :param sending: The sending speed
    :param server: The server
    :param price: The price
    """
    task.allocate(loading, compute, sending, server, price)
    server.allocate_task(task)


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
    print(f'Solve status: {model_solution.get_solve_status()}, Fail status: {model_solution.get_fail_status()}')
    print(f'Search status: {model_solution.get_search_status()}, Stop Cause: {model_solution.get_stop_cause()}, '
          f'Solve Time: {round(model_solution.get_solve_time(), 2)} secs')


def print_model(tasks: List[Task], servers: List[Server]):
    """
    Print the model

    :param tasks: The list of tasks
    :param servers: The list of servers
    """
    print('Job Name | Storage | Computation | Results Data | Value | Loading | Compute | Sending | Deadline | Price')
    for task in tasks:
        print(f'{task.name:^9s}|{task.required_storage:^9d}|{task.required_computation:^13d}|'
              f'{task.required_results_data:^14d}|{task.value:^7.1f}|{task.loading_speed:^9d}|{task.compute_speed:^9d}|'
              f'{task.sending_speed:^9d}|{task.deadline:^10d}| {task.price:.2f}')

    print('\nServer Name | Storage | Computation | Bandwidth | Allocated Jobs')
    for server in servers:
        print(f"{server.name:^12s}|{server.storage_capacity:^9d}|{server.computation_capacity:^13d}|"
              f"{server.bandwidth_capacity:^11d}| {', '.join([task.name for task in server.allocated_tasks])}")


# noinspection LongLine
def decode_filename(folder: str, filename: str) -> Tuple[str, str, str]:
    """
    Decodes the filename to recover the file location, the model name and the greedy name

    :param folder: The data folder
    :param filename: The encoded filename
    :return: Tuple of the location of the file and the model type
    """
    return f'../results/{folder}/{filename}.json', \
           re.findall(r'j\d+_s\d+', filename)[0].replace('_', ' ').replace('s', 'Servers: ').replace('t', 'Tasks: '), \
           filename.replace(re.findall(r'_j\d+_s\d+_\d+', filename)[0], '')


class ImageFormat(Enum):
    """
    Image format
    """
    EPS = auto()
    PNG = auto()
    PDF = auto()


def save_plot(name: str, test_name: str, additional: str = '',
              image_formats: Iterable[ImageFormat] = (), lgd=None):
    """
    Saves the plot to a file of the particular image format

    :param name: The plot name
    :param test_name: The test name
    :param additional: Additional information to add to the filename
    :param image_formats: The image format list
    :param lgd: The legend to be added to the plot when saved
    """
    if lgd:
        lgd = (lgd,)

    for image_format in image_formats:
        if image_format == ImageFormat.EPS:
            filename = f'../figures/{test_name}/eps/{name}{additional}.eps'
            print(f"Save file location: {filename}")
            plt.savefig(filename, format='eps', dpi=1000, bbox_extra_artists=lgd, bbox_inches='tight')
        elif image_format == ImageFormat.PNG:
            filename = f'../figures/{test_name}/png/{name}{additional}.png'
            print(f'Save file location: {filename}')
            plt.savefig(filename, format='png', bbox_extra_artists=lgd, bbox_inches='tight')
        elif image_format == ImageFormat.PDF:
            filename = f'../figures/{test_name}/eps/{name}{additional}.pdf'
            print(f'Save file location: {filename}')
            plt.savefig(filename, format='pdf', dpi=1000, bbox_extra_artists=lgd, bbox_inches='tight')


def set_price_change(servers: List[Server], price_change: int):
    """
    Sets the price change attribute on a list of servers

    :param servers: List of servers to affect
    :param price_change: Updated price change
    """
    for server in servers:
        server.price_change = price_change


def reset_model(tasks: List[Task], servers: List[Server], forgot_price: bool = True):
    """
    Resets all of the tasks and servers back after an allocation

    :param tasks: A list of tasks
    :param servers: A list of servers
    :param forgot_price: If to forgot the task price
    """
    for task in tasks:
        task.reset_allocation(forgot_price=forgot_price)

    for server in servers:
        server.reset_allocations()


def positive_gaussian_dist(mean, std) -> int:
    """
    Uses gaussian distribution to generate a random number greater than 0 for a resource

    :param mean: Gaussian mean
    :param std: Gaussian standard deviation
    :return: A float of random gaussian distribution
    """
    return max(1, int(gauss(mean, std)))
