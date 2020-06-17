"""Additional functions"""

from __future__ import annotations

from random import choice, gauss
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, List, TypeVar

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


def set_price_change(servers: List[Server], price_change: int):
    """
    Sets the price change attribute on a list of servers

    :param servers: List of servers to affect
    :param price_change: Updated price change
    """
    for server in servers:
        server.price_change = price_change


def reset_model(tasks: Iterable[Task], servers: Iterable[Server], forgot_price: bool = True):
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


def debug(message, case):
    if case:
        print(message)
