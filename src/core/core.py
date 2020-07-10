"""Additional functions"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from typing import Iterable, List

    from src.core.server import Server
    from src.core.task import Task


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


def reset_model(tasks: Iterable[Task], servers: Iterable[Server], forget_prices: bool = True):
    """
    Resets all of the tasks and servers back after an allocation

    :param tasks: A list of tasks
    :param servers: A list of servers
    :param forget_prices: If to forgot the task price
    """
    for task in tasks:
        task.reset_allocation(forget_price=forget_prices)

    for server in servers:
        server.reset_allocations()


def set_server_heuristics(servers: List[Server], price_change: Optional[int] = None,
                          initial_price: Optional[int] = None):
    """
    Sets the server heuristics (price change and initial price of all servers)

    :param servers: List of servers
    :param price_change: Price change
    :param initial_price: Initial price
    """
    for server in servers:
        if price_change is not None:
            server.price_change = price_change
        if initial_price is not None:
            server.initial_price = initial_price


def debug(message, case):
    """
    Debug a message

    :param message: The message
    :param case: If to print the message
    """
    if case:
        print(message)
