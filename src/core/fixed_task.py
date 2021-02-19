"""Fixed Task class"""

from __future__ import annotations

from abc import abstractmethod, ABC
from math import ceil
from typing import TYPE_CHECKING

from docplex.cp.model import CpoModel

from src.core.task import Task

if TYPE_CHECKING:
    from typing import Tuple

    from src.core.server import Server


class FixedTask(Task):
    """Task with a fixing resource usage speed"""

    def __init__(self, task: Task, fixed_value_policy: AllocationFixedPrioritisation, fixed_name: bool = True,
                 resource_foreknowledge: bool = False):
        name = f'Fixed {task.name}' if fixed_name else task.name

        self.fixed_value_policy = fixed_value_policy
        loading_speed, compute_speed, sending_speed = self.minimum_fixed_prioritisation(task, fixed_value_policy)
        if resource_foreknowledge is True:
            Task.__init__(self, name=name, required_storage=task.required_storage,
                          required_computation=task.required_computation,
                          required_results_data=task.required_results_data,
                          value=task.value, deadline=task.deadline, loading_speed=loading_speed,
                          compute_speed=compute_speed, sending_speed=sending_speed, auction_time=task.auction_time)
        else:
            assert task.planned_storage is not None and task.planned_computation is not None
            Task.__init__(self, name=name, required_storage=task.planned_storage,
                          required_computation=compute_speed, required_results_data=task.required_results_data,
                          value=task.value, deadline=task.deadline, auction_time=task.auction_time,
                          loading_speed=ceil(task.required_storage / loading_speed) * task.planned_storage,
                          compute_speed=ceil(task.required_computation / compute_speed) * task.planned_computation,
                          sending_speed=sending_speed)

    @staticmethod
    def minimum_fixed_prioritisation(task: Task,
                                     allocation_priority: AllocationFixedPrioritisation) -> Tuple[int, int, int]:
        """
        Find the optimal fixed speeds of the task

        :param task: The task to use
        :param allocation_priority: The fixed value function to value the speeds
        :return: Fixed speeds
        """
        model = CpoModel('FixedSpeedsPrioritisation')
        loading_speed = model.integer_var(min=1)
        compute_speed = model.integer_var(min=1)
        sending_speed = model.integer_var(min=1)

        model.add(task.required_storage / loading_speed +
                  task.required_computation / compute_speed +
                  task.required_results_data / sending_speed <= task.deadline)

        model.minimize(allocation_priority.evaluate(loading_speed, compute_speed, sending_speed))

        model_solution = model.solve(log_output=None)
        assert model_solution is not None
        assert 0 < model_solution.get_value(loading_speed) and \
            0 < model_solution.get_value(loading_speed) and \
            0 < model_solution.get_value(loading_speed)

        return model_solution.get_value(loading_speed), \
            model_solution.get_value(compute_speed), \
            model_solution.get_value(sending_speed)

    def allocate(self, loading_speed: int, compute_speed: int, sending_speed: int, running_server: Server,
                 price: float = None):
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

        if price is not None:
            self.price = price

    def reset_allocation(self, forget_price: bool = True):
        """
        Overrides the reset_allocation function from task to just change the server not resource speeds
        """
        self.running_server = None

        if forget_price:
            self.price = 0

    def batch(self, time_step):
        """
        Overrides the task batch function to update the deadline and task resource speeds to match
        :param time_step:
        :return:
        """
        # noinspection PyUnresolvedReferences
        batch_task = super().batch(time_step)
        return FixedTask(batch_task, self.fixed_value_policy, False)


class AllocationFixedPrioritisation(ABC):
    """
    Fixed Value policy for the fixed task to select the speed
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def evaluate(self, loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """
        Evaluate how good certain speeds

        :param loading_speed: Loading speed
        :param compute_speed: Compute speed
        :param sending_speed: Sending speed
        :return: value representing how good the resource speeds is
        """
        pass


class SumSpeedsFixedPrioritisation(AllocationFixedPrioritisation):
    """Fixed sum of speeds"""

    def __init__(self):
        AllocationFixedPrioritisation.__init__(self, 'Sum speeds')

    def evaluate(self, loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """Calculates the value by summing speeds"""
        return loading_speed + compute_speed + sending_speed


class SumSpeedPowFixedPrioritisation(AllocationFixedPrioritisation):
    """Fixed Exp Sum of speeds"""

    def __init__(self):
        AllocationFixedPrioritisation.__init__(self, 'Exp Sum Speeds')

    def evaluate(self, loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """Calculate the value by summing the expo of speeds"""
        return loading_speed ** 3 + compute_speed ** 3 + sending_speed ** 3

# TODO add more fixed value classes
