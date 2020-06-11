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

    def __init__(self, name: str, required_storage: int, required_computation: int, required_results_data: int,
                 value: float, deadline: int, loading_speed: int = 0, compute_speed: int = 0, sending_speed: int = 0,
                 running_server: Optional[Server] = None, price: float = 0):
        self.name = name

        self.required_storage = required_storage
        self.required_computation = required_computation
        self.required_results_data = required_results_data

        self.value = value
        self.price = price

        self.deadline = deadline

        self.loading_speed = loading_speed
        self.compute_speed = compute_speed
        self.sending_speed = sending_speed

        self.running_server = running_server

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
            f'Task {self.name} with loading {loading_speed} compute {compute_speed} sending {sending_speed}'

        # Python floats are overflowing causing errors, e.g. 2/3 + 1/3 != 1
        time_taken = self.required_storage * compute_speed * sending_speed + \
            loading_speed * self.required_computation * sending_speed + \
            loading_speed * compute_speed * self.required_results_data
        assert time_taken <= self.deadline * loading_speed * compute_speed * sending_speed, \
            f'Task {self.name} requirement storage {self.required_storage} computation {self.required_computation} ' \
            f'results data {self.required_results_data} with loading {loading_speed} compute {compute_speed} ' \
            f'sending {sending_speed} speed and deadline {self.deadline} time taken {time_taken}'

        # Check that a server is not already allocated
        assert self.running_server is None, f'Task {self.name} is already allocated to {self.running_server.name}'

        self.loading_speed = loading_speed
        self.compute_speed = compute_speed
        self.sending_speed = sending_speed
        self.running_server = running_server

        if price is not None:
            self.price = price

    def reset_allocation(self):
        """
        Resets the allocation data to the default
        """
        self.loading_speed = 0
        self.compute_speed = 0
        self.sending_speed = 0
        self.running_server = None
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
        return Task(f'mutated {self.name}',
                    int(self.required_storage + abs(gauss(0, self.required_storage * percent))),
                    int(self.required_computation + abs(gauss(0, self.required_computation * percent))),
                    int(self.required_results_data + abs(gauss(0, self.required_results_data * percent))),
                    int(max(1, self.deadline - abs(gauss(0, self.required_results_data * percent)))),
                    int(max(1, self.value - abs(gauss(0, self.required_results_data * percent)))))

    def __str__(self) -> str:
        if self.loading_speed > 0:
            return f'Task {self.name} - Required storage: {self.required_storage}, ' \
                   f'computation: {self.required_computation}, results data: {self.required_results_data}, ' \
                   f'deadline: {self.deadline}, value: {self.value}, allocated loading: {self.loading_speed}, ' \
                   f'compute: {self.compute_speed}, sending: {self.sending_speed} speeds'
        else:
            return f'Task {self.name} - Required storage: {self.required_storage}, ' \
                   f'computation: {self.required_computation}, results data: {self.required_results_data}, ' \
                   f'deadline: {self.deadline}, value: {self.value}'


def task_diff(normal_task: Task, mutate_task: Task) -> str:
    """
    The difference in task attributes between a normal and mutated task

    :param normal_task: normal task
    :param mutate_task: mutated task
    :return: String representing the task attributes between tasks
    """
    return f"{normal_task.name} - {mutate_task.name}: {mutate_task.required_storage - normal_task.required_storage}, {mutate_task.required_computation - normal_task.required_computation}, {mutate_task.required_results_data - normal_task.required_results_data}, {normal_task.deadline - mutate_task.deadline}, {normal_task.value - mutate_task.value}"
