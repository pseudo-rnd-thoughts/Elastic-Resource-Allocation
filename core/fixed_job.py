"""Fixed Job class"""

from __future__ import annotations

from abc import abstractmethod, ABC
from typing import List

from docplex.cp.model import CpoModel

from core.job import Job
from core.server import Server


class FixedJob(Job):
    """Job with a fixing resource usage speed"""

    def __init__(self, job: Job, servers: List[Server], fixed_value: FixedValue):
        super().__init__("Fixed " + job.name, job.required_storage, job.required_computation, job.required_results_data,
                         job.value, job.deadline)
        self.original_job = job
        self.loading_speed, self.compute_speed, self.sending_speed = self.find_fixed_speeds(servers, fixed_value)

    def find_fixed_speeds(self, servers: List[Server], fixed_value: FixedValue):
        model = CpoModel("Speeds")
        loading_speed = model.integer_var(min=1, max=max(server.bandwidth_capacity for server in servers) - 1)
        compute_speed = model.integer_var(min=1, max=max(server.storage_capacity for server in servers))
        sending_speed = model.integer_var(min=1, max=max(server.bandwidth_capacity for server in servers) - 1)

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
        Overrides the allocate function from job to just allocate the running server and the price
        :param loading_speed: Ignored
        :param compute_speed: Ignored
        :param sending_speed: Ignored
        :param running_server: The server the job is running on
        :param price: The price of the job
        """
        assert self.running_server is None

        self.running_server = running_server
        self.price = price

    def reset_allocation(self):
        """
        Overrides the reset_allocation function from job to just change the server not resource speeds
        """
        self.running_server = None


class FixedValue(ABC):
    """
    Fixed Value policy for the fixed job to select the speed
    """

    def __init__(self, name):
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
        super().__init__("Sum speeds")

    def evaluate(self, loading_speed: int, compute_speed: int, sending_speed: int) -> int:
        """Evaluation of how good it is"""
        return loading_speed + compute_speed + sending_speed

# TODO add more fixed value classes
