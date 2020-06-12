"""Task object implementation"""

from __future__ import annotations

from random import gauss
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.server import Server


class Task(object):
    """
    Task object with name and required resources to use (storage, computation and models data)
    When the task is allocated to a server then the resources speed and server are set

    Constructor arguments are final as they dont need changing after initialisation
    """

    # Allocation information
    loading_speed: int = 0
    compute_speed: int = 0
    sending_speed: int = 0
    running_server: Optional[Server] = None

    price: float = 0  # This is for auctions only

    def __init__(self, name: str, required_storage: int, required_computation: int, required_results_data: int,
                 value: float, deadline: int):
        self.name: str = name
        self.required_storage: int = required_storage
        self.required_computation: int = required_computation
        self.required_results_data: int = required_results_data
        self.value: float = value
        self.deadline: int = deadline

    def allocate(self, loading_speed: int, compute_speed: int, sending_speed: int, running_server: Server,
                 price: float = None):
        """
        Sets the task attribute for when it is allocated to a server
        :param loading_speed: The loading speed of the task
        :param compute_speed: The computational speed of the task
        :param sending_speed: The sending speed of the tasks
        :param running_server: The server the task is running on
        :param price: The price of the task
        """
        # Check that the allocation information is correct
        assert loading_speed > 0 and compute_speed > 0 and sending_speed > 0, \
            "Allocation information is incorrect for Task {} with loading {} compute {} sending {}" \
            .format(self.name, loading_speed, compute_speed, sending_speed)

        # Python floats are overflowing causing errors, e.g. 2/3 + 1/3 != 1
        assert self.required_storage * compute_speed * sending_speed + \
            loading_speed * self.required_computation * sending_speed + \
            loading_speed * compute_speed * self.required_results_data <= \
            self.deadline * loading_speed * compute_speed * sending_speed, \
            "Deadline assertion failure Task {} requirement storage {} computation {} results data {} " \
            "with loading {} compute {} sending {} speed and deadline {} time taken {}" \
                .format(self.name, self.required_storage, self.required_computation, self.required_results_data,
                        loading_speed, compute_speed, sending_speed, self.deadline,
                        self.required_storage * compute_speed * sending_speed +
                        loading_speed * self.required_computation * sending_speed +
                        loading_speed * compute_speed * self.required_results_data)

        # Check that a server is not already allocated
        assert self.running_server is None, \
            "Task {} is already allocated to {}".format(self.name, self.running_server.name)

        self.loading_speed = loading_speed
        self.compute_speed = compute_speed
        self.sending_speed = sending_speed
        self.running_server = running_server

        if price is not None:
            self.price = round(price, 3)

    def reset_allocation(self, forgot_price: bool = True):
        """
        Resets the allocation data to the default
        """
        self.loading_speed = 0
        self.compute_speed = 0
        self.sending_speed = 0
        self.running_server = None

        if forgot_price:
            self.price = 0

    def utility(self):
        """
        The social welfare of the task
        :return: The task value minus task price
        """
        return self.value - self.price

    def mutate(self, percent) -> Task:
        """
        Mutate the server by a percentage
        :param percent: The percentage to increase the max resources by
        """
        return Task('mutated {}'.format(self.name),
                    int(self.required_storage + abs(gauss(0, self.required_storage * percent))),
                    int(self.required_computation + abs(gauss(0, self.required_computation * percent))),
                    int(self.required_results_data + abs(gauss(0, self.required_results_data * percent))),
                    int(max(1, self.deadline - abs(gauss(0, self.required_results_data * percent)))),
                    int(max(1, self.value - abs(gauss(0, self.required_results_data * percent)))))

    def __str__(self) -> str:
        if self.loading_speed > 0:
            return "Task {} - Required storage: {}, computation: {}, results data: {}, deadline: {}, value: {}, " \
                   "allocated loading: {}, compute: {}, sending: {} speeds" \
                .format(self.name, self.required_storage, self.required_computation, self.required_results_data,
                        self.deadline, self.value, self.loading_speed, self.compute_speed, self.sending_speed)
        else:
            return "Task {} - Required storage: {}, computation: {}, results data: {}, deadline: {}, value: {}" \
                .format(self.name, self.required_storage, self.required_computation, self.required_results_data,
                        self.deadline, self.value)


def task_diff(normal_task: Task, mutate_task: Task) -> str:
    """The difference between two tasks"""
    return "{} - {}: {}, {}, {}, {}, {}".format(normal_task.name, mutate_task.name,
                                                mutate_task.required_storage - normal_task.required_storage,
                                                mutate_task.required_computation - normal_task.required_computation,
                                                mutate_task.required_results_data - normal_task.required_results_data,
                                                normal_task.deadline - mutate_task.deadline,
                                                normal_task.value - mutate_task.value)
