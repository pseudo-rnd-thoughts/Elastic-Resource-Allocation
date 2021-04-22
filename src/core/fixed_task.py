"""Fixed Task class"""

from __future__ import annotations

import sys
import time
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, List

from docplex.cp.model import CpoModel, SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL

from src.core.task import Task

if TYPE_CHECKING:
    from typing import Tuple

    from src.core.server import Server


class FixedTask(Task):
    """Task with a fixing resource usage speed"""

    def __init__(self, task: Task, fixed_value_policy: FixedAllocationPriority, fixed_name: bool = True):
        name = f'Fixed {task.name}' if fixed_name else task.name

        self.fixed_value_policy = fixed_value_policy
        loading_speed, compute_speed, sending_speed = self.minimum_fixed_prioritisation(task, fixed_value_policy)

        Task.__init__(self, name=name, required_storage=task.required_storage,
                      required_computation=task.required_computation,
                      required_results_data=task.required_results_data,
                      value=task.value, deadline=task.deadline, auction_time=task.auction_time,
                      loading_speed=loading_speed, compute_speed=compute_speed, sending_speed=sending_speed)

    @staticmethod
    def minimum_fixed_prioritisation(task: Task, allocation_priority: FixedAllocationPriority) -> Tuple[int, int, int]:
        """
        Find the optimal fixed speeds of the task

        :param task: The task to use
        :param allocation_priority: The fixed value function to value the speeds
        :return: Fixed speeds
        """
        model = CpoModel('FixedSpeedsPrioritisation')
        loading_speed = model.integer_var(min=1, name='loading speed')
        compute_speed = model.integer_var(min=1, name='compute speed')
        sending_speed = model.integer_var(min=1, name='sending speed')

        model.add(task.required_storage / loading_speed +
                  task.required_computation / compute_speed +
                  task.required_results_data / sending_speed <= task.deadline)

        model.minimize(allocation_priority.evaluate(loading_speed, compute_speed, sending_speed))

        model_solution = model.solve(log_output=None)
        assert model_solution.get_solve_status() == SOLVE_STATUS_FEASIBLE or \
            model_solution.get_solve_status() == SOLVE_STATUS_OPTIMAL, \
            (model_solution.get_solve_status(), task.__str__())
        assert 0 < model_solution.get_value(loading_speed) and \
            0 < model_solution.get_value(compute_speed) and \
            0 < model_solution.get_value(sending_speed), \
            (model_solution.get(loading_speed), model_solution.get(compute_speed), model_solution.get(sending_speed))

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


class FixedAllocationPriority(ABC):
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


class SumSpeedsFixedAllocationPriority(FixedAllocationPriority):
    """Fixed sum of speeds"""

    def __init__(self):
        FixedAllocationPriority.__init__(self, 'Sum speeds')

    def evaluate(self, loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """Calculates the value by summing speeds"""
        return loading_speed + compute_speed + sending_speed


class SumSpeedPowFixedAllocationPriority(FixedAllocationPriority):
    """Fixed Exp Sum of speeds"""

    def __init__(self):
        FixedAllocationPriority.__init__(self, 'Exp Sum Speeds')

    def evaluate(self, loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """Calculate the value by summing the expo of speeds"""
        return loading_speed ** 3 + compute_speed ** 3 + sending_speed ** 3


# TODO add more fixed value classes


def generate_fixed_tasks(tasks: List[Task], max_tries: int = 5,
                         priority: FixedAllocationPriority = SumSpeedsFixedAllocationPriority()) -> List[FixedTask]:
    """
    Generates a list of fixed tasks catching if the generation of the task fails for some reasons

    :param tasks: List of tasks
    :param priority: Fixed allocation priority class
    :param max_tries: The max tries for generated the fixed task
    :return: A list of fixed tasks
    """
    fixed_tasks = []
    for task in tasks:
        tries = 0
        while tries < max_tries:
            try:
                fixed_task = FixedTask(task, priority)
                fixed_tasks.append(fixed_task)
                break
            except Exception as e:
                print(e, file=sys.stderr)
                tries += 1
                time.sleep(0.5)
        if tries == max_tries:
            raise Exception(f'Unable to create the fixed task {task.__str__()}')
    return fixed_tasks
