"""Server object implementation"""

from __future__ import annotations

from random import gauss
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.task import Task


class Server(object):
    """
    Server object with a name and resources allocated
    """

    revenue: float = 0  # This is the total price of the task's allocated
    value: float = 0  # This is the total value of the task's allocated

    def __init__(self, name: str, storage_capacity: int, computation_capacity: int, bandwidth_capacity: int,
                 price_change: int = 1):
        self.name: str = name
        self.storage_capacity: int = storage_capacity
        self.computation_capacity: int = computation_capacity
        self.bandwidth_capacity: int = bandwidth_capacity
        self.price_change: int = price_change

        # Allocation information
        self.allocated_tasks: List[Task] = []
        self.available_storage: int = storage_capacity
        self.available_computation: int = computation_capacity
        self.available_bandwidth: int = bandwidth_capacity

    def can_run(self, task: Task) -> bool:
        """
        Checks if a task can be run on a server if it dedicates all of it's available resources to the task

        :param task: The task to test
        :return: If it can run
        """
        return self.available_storage >= task.required_storage \
            and self.available_computation >= 1 \
            and self.available_bandwidth >= 2 and \
            any(task.required_storage * self.available_computation * r + s * task.required_computation * r +
                s * self.available_computation * task.required_results_data
                <= task.deadline * s * self.available_computation * r
                for s in range(1, self.available_bandwidth + 1)
                for r in range(1, self.available_bandwidth - s + 1))

    # noinspection DuplicatedCode
    def can_empty_run(self, task: Task) -> bool:
        """
        Checks if a task can be run on a server if it dedicates all of it's possible resources to the task

        :param task: The task to test
        :return: If it can run
        """
        return self.storage_capacity >= task.required_storage \
            and self.computation_capacity >= 1 \
            and self.bandwidth_capacity >= 2 and \
            any(task.required_storage * self.computation_capacity * r +
                s * task.required_computation * r +
                s * self.computation_capacity * task.required_results_data
                <= task.deadline * s * self.available_computation * r
                for s in range(1, self.bandwidth_capacity + 1)
                for r in range(1, self.bandwidth_capacity - s + 1))

    def allocate_task(self, task: Task):
        """
        Updates the server attributes for when it is allocated within tasks

        :param task: The task being allocated
        """
        assert task.loading_speed > 0 and task.compute_speed > 0 and task.sending_speed > 0, \
            f'Task {task.name} - loading: {task.loading_speed}, compute: {task.compute_speed}, sending: {task.sending_speed}'
        assert self.available_storage >= task.required_storage, \
            f'Server {self.name} available storage {self.available_storage}, task required storage {task.required_storage}'
        assert self.available_computation >= task.compute_speed, \
            f'Server {self.name} available computation {self.available_computation}, task compute speed {task.compute_speed}'
        assert self.available_bandwidth >= task.loading_speed + task.sending_speed, \
            f'Server {self.name} available bandwidth {self.available_bandwidth}, ' \
            f'task loading speed {task.loading_speed} and sending speed {task.sending_speed}'
        assert task not in self.allocated_tasks, f'Task {task.name} is already allocated to the server {self.name}'

        self.allocated_tasks.append(task)
        self.available_storage -= task.required_storage
        self.available_computation -= task.compute_speed
        self.available_bandwidth -= (task.loading_speed + task.sending_speed)

        self.revenue += task.price
        self.value += task.value

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

    def mutate(self, percent) -> Server:
        """
        Mutate the server by a percentage

        :param percent: The percentage to increase the max resources by
        """
        return Server(f'mutated {self.name}',
                      int(max(1, self.storage_capacity - abs(gauss(0, self.storage_capacity * percent)))),
                      int(max(1, self.computation_capacity - abs(gauss(0, self.computation_capacity * percent)))),
                      int(max(1, self.bandwidth_capacity - abs(gauss(0, self.bandwidth_capacity * percent)))),
                      self.price_change)


def server_diff(normal_server: Server, mutate_server: Server) -> str:
    """
    The difference in server attributes between two servers

    :param normal_server: The normal server
    :param mutate_server: The mutated server
    :return: String representing the difference between two servers
    """
    return f'{normal_server.name}: {normal_server.storage_capacity - mutate_server.storage_capacity}, ' \
           f'{normal_server.computation_capacity - mutate_server.computation_capacity}, ' \
           f'{normal_server.bandwidth_capacity - mutate_server.bandwidth_capacity}'
