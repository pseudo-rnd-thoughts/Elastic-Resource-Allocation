"""Additional functions"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, List

    from core.server import Server
    from core.task import Task


def server_task_allocation(server: Server, task: Task, loading: int, compute: int, sending: int, price: float = None):
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


def set_price_change(servers: List[Server], price_change: int):
    """
    Sets the price change attribute on a list of servers

    :param servers: List of servers to affect
    :param price_change: Updated price change
    """
    for server in servers:
        server.price_change = price_change


def set_initial_price(servers: List[Server], initial_price: int):
    """
    Sets the initial price attribute on a list of servers

    :param servers: List of servers to affect
    :param initial_price: Updated initial price
    """
    for server in servers:
        server.initial_price = initial_price


def debug(message, case):
    """
    Debug a message

    :param message: The message
    :param case: If to print the message
    """
    if case:
        print(message)
