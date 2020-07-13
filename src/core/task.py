"""Task object implementation"""

from __future__ import annotations

from random import gauss
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Dict, Any

    from src.core.server import Server


class Task:
    """
    Task object with name and required resources to use (storage, computation and models data)
    When the task is allocated to a server then the resources speed and server are set

    Constructor arguments are final as they dont need changing after initialisation
    """

    def __init__(self, name: str, required_storage: int, required_computation: int, required_results_data: int,
                 value: float, deadline: int, loading_speed: int = 0, compute_speed: int = 0, sending_speed: int = 0,
                 running_server: Optional[Server] = None, price: float = 0, auction_time: int = -1):
        self.name = name

        self.required_storage = required_storage
        self.required_computation = required_computation
        self.required_results_data = required_results_data

        self.value = value  # This is the true private internal evaluation (the max price)
        self.price = price  # This is only used for auctions

        self.auction_time = auction_time  # This is only used for online vs batched evaluation
        self.deadline = deadline

        # Allocation information
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
        assert 0 < loading_speed and 0 < compute_speed and 0 < sending_speed, \
            f'Allocation information is incorrect for Task {self.name} with loading {loading_speed} ' \
            f'compute {compute_speed} sending {sending_speed}'

        # Python floats are overflowing causing errors, e.g. 2/3 + 1/3 != 1
        time_taken = self.required_storage * compute_speed * sending_speed + \
            loading_speed * self.required_computation * sending_speed + \
            loading_speed * compute_speed * self.required_results_data
        assert time_taken <= self.deadline * loading_speed * compute_speed * sending_speed, \
            f'Deadline assertion failure Task {self.name} requirement storage {self.required_storage} ' \
            f'computation {self.required_computation} results data {self.required_results_data} with ' \
            f'loading {loading_speed} compute {compute_speed} sending {sending_speed} speed and deadline {self.deadline} ' \
            f'time taken {time_taken}'

        # Check that a server is not already allocated
        assert self.running_server is None, f"Task {self.name} is already allocated to {self.running_server.name}"

        self.loading_speed = loading_speed
        self.compute_speed = compute_speed
        self.sending_speed = sending_speed
        self.running_server = running_server

        if price is not None:
            self.price = round(price, 3)

    def reset_allocation(self, forget_price: bool = True):
        """
        Resets the allocation data to the default
        """
        self.loading_speed = 0
        self.compute_speed = 0
        self.sending_speed = 0
        self.running_server = None

        if forget_price:
            self.price = 0

    @property
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
                    int(max(1, self.deadline - abs(gauss(0, self.deadline * percent)))),
                    int(max(1, self.value - abs(gauss(0, self.value * percent)))))

    def save(self):
        """
        Saves the task attributes to a dictionary

        :return: Dictionary representing the task attributes
        """
        save_spec = {
            'name': self.name,
            'storage': self.required_storage,
            'computation': self.required_computation,
            'results data': self.required_results_data,
            'deadline': self.deadline,
            'value': self.value
        }
        if 0 < self.auction_time:
            save_spec.update({'auction time': self.auction_time})

        return save_spec

    def __str__(self) -> str:
        if self.loading_speed > 0 and self.compute_speed > 0 and self.sending_speed > 0:
            return f'{self.name} Task - Required storage: {self.required_storage}, ' \
                   f'computation: {self.required_computation}, results data: {self.required_results_data}, ' \
                   f'deadline: {self.deadline}, value: {self.value}, allocated loading: {self.loading_speed}, ' \
                   f'compute: {self.compute_speed}, sending: {self.sending_speed} speeds'
        else:
            return f'{self.name} Task - Required storage: {self.required_storage}, ' \
                   f'computation: {self.required_computation}, results data: {self.required_results_data}, ' \
                   f'deadline: {self.deadline}, value: {self.value}'

    @staticmethod
    def load(task_spec: Dict[str, Any]) -> Task:
        """
        Loads task's specifications

        :param task_spec: Task specifications
        :return: A new task from the specifications
        """
        return Task(
            name=task_spec['name'], required_storage=task_spec['storage'],
            required_computation=task_spec['computation'], required_results_data=task_spec['results data'],
            deadline=task_spec['deadline'], value=task_spec['value'],
            auction_time=task_spec['auction time'] if 'auction time' in task_spec else 0
        )

    @staticmethod
    def load_dist(task_dist: Dict[str, Any], task_id: int) -> Task:
        """
        Loads a task from a task distribution

        :param task_dist: A JSON dictionary representing task distribution
        :param task_id: A task identifier value
        :return: A new task based on a task distribution
        """

        def positive_gaussian(mean, std) -> int:
            """
            Uses gaussian distribution to generate a random number greater than 0 for a resource

            :param mean: Gaussian mean
            :param std: Gaussian standard deviation
            :return: A float of random gaussian distribution
            """
            return max(1, int(gauss(mean, std)))

        return Task(
            name=f'{task_dist["name"]} {task_id}',
            required_storage=positive_gaussian(task_dist['storage mean'], task_dist['storage std']),
            required_computation=positive_gaussian(task_dist['computation mean'], task_dist['computation std']),
            required_results_data=positive_gaussian(task_dist['results data mean'], task_dist['results data std']),
            deadline=positive_gaussian(task_dist['deadline mean'], task_dist['deadline std']),
            value=positive_gaussian(task_dist['value mean'], task_dist['value std'])
        )

    def batch(self, time_step):
        """
        Returns a new batched task based on the time step, auction time and deadline

        :param time_step: The time step where a batch starts
        :return: A new task
        """
        return Task(
            name=self.name,
            required_storage=self.required_storage,
            required_computation=self.required_computation,
            required_results_data=self.required_results_data,
            value=self.value,
            auction_time=self.auction_time,
            deadline=self.deadline - (time_step - self.auction_time)
        )
