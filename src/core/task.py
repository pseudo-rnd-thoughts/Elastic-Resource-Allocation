"""Task object implementation"""

from __future__ import annotations

from math import ceil
from random import gauss, randint, uniform
from typing import TYPE_CHECKING, List

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
                 deadline: int, value: Optional[float] = None, price: float = 0, auction_time: int = -1,
                 loading_speed: Optional[int] = None, compute_speed: Optional[int] = None,
                 sending_speed: Optional[int] = None,
                 running_server: Optional[Server] = None, servers: List[Server] = None):
        # Name of the task
        self.name = name

        # The required resources over the task's lifetime
        self.required_storage = required_storage
        self.required_computation = required_computation
        self.required_results_data = required_results_data

        # This is the true private internal evaluation (the max price) and the price that the task runs for
        self.value = self.concave_value(servers) if value is None else value
        self.price = price

        # This is only used for online vs batched evaluation
        self.auction_time = auction_time
        self.deadline = deadline

        # Server who the task is allocated to
        self.running_server = running_server

        # Allocation information
        if loading_speed is None and compute_speed is None and sending_speed is None:
            self.loading_speed, self.compute_speed, self.sending_speed = 0, 0, 0
        else:
            assert 0 < loading_speed and 0 < compute_speed and 0 < sending_speed, \
                (loading_speed, compute_speed, sending_speed)
            self.loading_speed, self.compute_speed, self.sending_speed = loading_speed, compute_speed, sending_speed

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
            f'loading {loading_speed} compute {compute_speed} sending {sending_speed} speed and ' \
            f'deadline {self.deadline} time taken {time_taken}'

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

    def mutate(self, mutation_percent) -> Task:
        """
        Mutate the server by a percentage
        
        :param mutation_percent: The percentage to increase the max resources by
        """
        return Task(name=f'mutated {self.name}',
                    required_storage=randint(self.required_storage,
                                             ceil(self.required_storage * (1 + mutation_percent))),
                    required_computation=randint(self.required_computation,
                                                 ceil(self.required_computation * (1 + mutation_percent))),
                    required_results_data=randint(self.required_results_data,
                                                  ceil(self.required_results_data * (1 + mutation_percent))),
                    deadline=max(1, randint(ceil(self.deadline * (1 - mutation_percent)), self.deadline)),
                    value=self.value)

    def save(self, more=False):
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
        if 0 <= self.auction_time:
            save_spec.update({'auction time': self.auction_time})
        if more:
            save_spec.update({'loading speed': self.loading_speed, 'compute speed': self.compute_speed,
                              'sending speed': self.sending_speed})

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
    def load_dist(task_dist: Dict[str, Any], task_id: int, servers: List[Server]) -> Task:
        """
        Loads a task from a task distribution

        :param task_dist: A JSON dictionary representing task distribution
        :param task_id: A task identifier value
        :param servers: list of servers
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
            value=None, servers=servers)

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

    def loading_ub(self):
        """
        Reasonable values for the upper bound of the loading speed for the task in order to speed cplex and reduce
            wasted resources

        :return: Reasonable upper bound for the loading speed
        """
        return ceil(5 * self.required_storage / self.deadline)

    def compute_ub(self):
        """
        Reasonable values for the upper bound of the compute speed for the task in order to speed cplex and reduce
            wasted resources

        :return: Reasonable upper bound for the compute speed
        """
        return ceil(5 * self.required_computation / self.deadline)

    def sending_ub(self):
        """
        Reasonable values for the upper bound of the sending speed for the task in order to speed cplex and reduce
            wasted resources

        :return: Reasonable upper bound for the sending speed
        """
        return ceil(5 * self.required_results_data / self.deadline)

    def concave_value(self, servers: List[Server]):
        """
        Generates a concave utility in accordance with Araldo et al, 2020

        :param servers: List of servers to get the maximum resources
        :return: value of the task
        """
        alpha, alpha_prime = uniform(0, 1), uniform(0, 1)
        if alpha_prime < alpha:
            alpha, alpha_prime = alpha_prime, alpha
        beta_storage, beta_comp, beta_results_data = uniform(1, 5), uniform(1, 5), uniform(1, 5)

        storage_total = sum(server.storage_capacity for server in servers)
        comp_total = sum(server.computation_capacity for server in servers)
        results_total = sum(server.bandwidth_capacity for server in servers)

        storage_value = alpha * pow(self.required_storage / storage_total, 1 / beta_storage)
        computation_value = (alpha_prime - alpha) * pow(self.required_computation / comp_total, 1 / beta_comp)
        results_data_value = (1 - alpha_prime) * pow(self.required_results_data / results_total, 1 / beta_results_data)
        return round(storage_value + computation_value + results_data_value * 100, 2)
