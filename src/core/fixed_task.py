"""Fixed Task class"""

from __future__ import annotations

from abc import abstractmethod, ABC
from typing import List

from docplex.cp.model import CpoModel

from src.core.server import Server
from src.core.task import Task


class FixedTask(Task):
    """Task with a fixing resource usage speed"""

    def __init__(self, task: Task, servers: List[Server], fixed_value: FixedValue):
        Task.__init__(self, task.name, task.required_storage, task.required_computation, task.required_results_data,
                      task.value, task.deadline)
        self.original_task = task
        self.loading_speed, self.compute_speed, self.sending_speed = self.find_fixed_speeds(servers, fixed_value)

    def find_fixed_speeds(self, servers: List[Server], fixed_value: FixedValue):
        """
        Finds the optimal fixed task speeds based on the fixed value function

        :param servers: List of servers to know max values to speed search
        :param fixed_value: The fixed value function for objective function
        :return: Optimal loading, compute and sending speeds
        """
        model = CpoModel('Speeds')
        loading_speed: int = model.integer_var(min=1, max=max(server.bandwidth_capacity for server in servers) - 1)
        compute_speed: int = model.integer_var(min=1, max=max(server.storage_capacity for server in servers))
        sending_speed: int = model.integer_var(min=1, max=max(server.bandwidth_capacity for server in servers) - 1)

        model.add(self.required_storage / loading_speed +
                  self.required_computation / compute_speed +
                  self.required_results_data / sending_speed <= self.deadline)

        model.minimize(fixed_value.evaluate(loading_speed, compute_speed, sending_speed))

        model_solution = model.solve(log_output=None)

        return model_solution.get_value(loading_speed), \
            model_solution.get_value(compute_speed), \
            model_solution.get_value(sending_speed)

    def allocate(self, loading_speed: int, compute_speed: int, sending_speed: int, running_server: Server,
                 price: float = 0):
        """
        Overrides the allocate function from task to just allocate the running server and the price

        :param loading_speed: Ignored
        :param compute_speed: Ignored
        :param sending_speed: Ignored
        :param running_server: The server the task is running on
        :param price: The price of the task
        """
        assert self.running_server is None

        self.running_server = running_server
        self.price = price

    def reset_allocation(self):
        """
        Overrides the reset_allocation function from task to just change the server not resource speeds
        """
        self.running_server = None


class FixedValue(ABC):
    """
    Fixed Value policy for the fixed task to select the speed
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def evaluate(self, loading_speed: int, compute_speed: int, sending_speed: int) -> int:
        """
        Evaluate how good certain speeds

        :param loading_speed: Loading speed
        :param compute_speed: Compute speed
        :param sending_speed: Sending speed
        :return: How good it is
        """
        pass


class FixedSumSpeeds(FixedValue):
    """Fixed sum of speeds"""

    def __init__(self):
        FixedValue.__init__(self, 'Sum speeds')

    def evaluate(self, loading_speed: int, compute_speed: int, sending_speed: int) -> int:
        """Evaluation of how good it is"""
        return loading_speed + compute_speed + sending_speed

# TODO add more fixed value classes
