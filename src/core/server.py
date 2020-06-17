"""Server object implementation"""

from __future__ import annotations

from random import gauss
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List

    from core.task import Task


class Server:
    """
    Server object with a name and resources allocated
    """

    revenue: float = 0  # This is the total price of the task's allocated
    value: float = 0  # This is the total value of the task's allocated

    def __init__(self, name: str, storage_capacity: int, computation_capacity: int, bandwidth_capacity: int,
                 price_change: int = 1, initial_price: int = 0):
        self.name: str = name

        self.storage_capacity: int = storage_capacity
        self.computation_capacity: int = computation_capacity
        self.bandwidth_capacity: int = bandwidth_capacity

        self.price_change: int = price_change
        self.initial_price: int = initial_price

        # Allocation information
        self.allocated_tasks: List[Task] = []
        self.available_storage: int = storage_capacity
        self.available_computation: int = computation_capacity
        self.available_bandwidth: int = bandwidth_capacity

    # noinspection DuplicatedCode
    def can_run(self, task: Task) -> bool:
        """
        Checks if a task can be run on a server if it dedicates all of it's available resources to the task

        :param task: The task to test
        :return: If it can run
        """

        if not (task.required_storage <= self.available_storage and
                self.available_bandwidth >= 2 and self.available_computation >= 1):
            return False

        for s in range(1, self.available_bandwidth):
            if task.required_storage * self.available_computation * (self.available_bandwidth - s) + \
                    s * task.required_computation * (self.available_bandwidth - s) + \
                    s * self.available_computation * task.required_results_data <= \
                    task.deadline * s * self.available_computation * (self.available_bandwidth - s):
                return True
        return False

    # noinspection DuplicatedCode
    def can_empty_run(self, task: Task) -> bool:
        """
        Checks if a task can be run on a server if it dedicates all of it's possible resources to the task

        :param task: The task to test
        :return: If it can run
        """

        if not (task.required_storage <= self.storage_capacity and
                self.bandwidth_capacity >= 2 and self.computation_capacity >= 1):
            return False

        for s in range(1, self.bandwidth_capacity):
            if task.required_storage * self.computation_capacity * (self.bandwidth_capacity - s) + \
                    s * task.required_computation * (self.bandwidth_capacity - s) + \
                    s * self.computation_capacity * task.required_results_data <= \
                    task.deadline * s * self.computation_capacity * (self.bandwidth_capacity - s):
                return True
        return False

    def allocate_task(self, task: Task):
        """
        Updates the server attributes for when it is allocated within tasks

        :param task: The task being allocated
        """
        assert task.loading_speed > 0 and task.compute_speed > 0 and task.sending_speed > 0, \
            f'Job speed failure for Job {task.name} - loading: {task.loading_speed}, ' \
            f'compute: {task.compute_speed}, sending: {task.sending_speed}'
        assert self.available_storage >= task.required_storage, \
            f'Server storage failure for Server {self.name} available storage {self.available_storage}, ' \
            f'task required storage {task.required_storage}'
        assert self.available_computation >= task.compute_speed, \
            f'Server computation failure for Server {self.name} available computation {self.available_computation}, ' \
            f'task compute speed {task.compute_speed}'
        assert self.available_bandwidth >= task.loading_speed + task.sending_speed, \
            f'Server available bandwidth failure for Server {self.name} available bandwidth {self.available_bandwidth}, ' \
            f'task loading speed {task.loading_speed} and sending speed {task.sending_speed}'
        assert task not in self.allocated_tasks, \
            f'Job {task.name} is already allocated to the server {self.name}'

        self.allocated_tasks.append(task)
        self.available_storage -= task.required_storage
        self.available_computation -= task.compute_speed
        self.available_bandwidth -= (task.loading_speed + task.sending_speed)

        self.revenue += task.price

    def reset_allocations(self):
        """
        Resets the allocation information
        """
        self.allocated_tasks = []

        self.available_storage = self.storage_capacity
        self.available_computation = self.computation_capacity
        self.available_bandwidth = self.bandwidth_capacity

        self.revenue = 0
        self.value = 0

    def mutate(self, percent: float) -> Server:
        """
        Mutate the server by a percentage

        :param percent: The percentage to increase the max resources by
        """
        return Server(f'mutated {self.name}',
                      int(max(1, self.storage_capacity - abs(gauss(0, self.storage_capacity * percent)))),
                      int(max(1, self.computation_capacity - abs(gauss(0, self.computation_capacity * percent)))),
                      int(max(1, self.bandwidth_capacity - abs(gauss(0, self.bandwidth_capacity * percent)))),
                      self.price_change)

    def update_capacities(self, computation_capacity: int, bandwidth_capacity: int):
        """
        Update the computational and bandwidth capacities of the server

        :param computation_capacity: The new computational capacity
        :param bandwidth_capacity: The new bandwidth capacity
        """
        self.computation_capacity = computation_capacity
        self.available_computation = computation_capacity

        self.bandwidth_capacity = bandwidth_capacity
        self.available_bandwidth = bandwidth_capacity


def server_diff(normal_server: Server, mutate_server: Server) -> str:
    """The difference between two severs"""
    return f'{normal_server.name}: {normal_server.storage_capacity - mutate_server.storage_capacity}, ' \
           f'{normal_server.computation_capacity - mutate_server.computation_capacity}, ' \
           f'{normal_server.bandwidth_capacity - mutate_server.bandwidth_capacity}'
