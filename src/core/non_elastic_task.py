"""Non elastic task class"""

from __future__ import annotations

import sys
import time
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, List

from docplex.cp.model import CpoModel, SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL

from src.core.elastic_task import ElasticTask

if TYPE_CHECKING:
    from typing import Tuple

    from src.core.server import Server


class NonElasticTask(ElasticTask):
    """Task with a non-elastic resource usage speed"""

    def __init__(self, task: ElasticTask, non_elastic_value_policy: NonElasticResourcePriority,
                 non_elastic_name: bool = True):
        name = f'Non Elastic {task.name}' if non_elastic_name else task.name

        self.non_elastic_value_policy = non_elastic_value_policy
        loading_speed, compute_speed, sending_speed = self.minimum_resources(task, non_elastic_value_policy)

        ElasticTask.__init__(self, name=name, required_storage=task.required_storage,
                             required_computation=task.required_computation,
                             required_results_data=task.required_results_data,
                             value=task.value, deadline=task.deadline, auction_time=task.auction_time,
                             loading_speed=loading_speed, compute_speed=compute_speed, sending_speed=sending_speed)

    @staticmethod
    def minimum_resources(task: ElasticTask, allocation_priority: NonElasticResourcePriority) -> Tuple[int, int, int]:
        """
        Find the optimal non_elastic speeds of the task

        :param task: The task to use
        :param allocation_priority: The non-elastic value function to value the speeds
        :return: non_elastic speeds
        """
        model = CpoModel('non_elasticSpeedsPrioritisation')
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
        return NonElasticTask(batch_task, self.non_elastic_value_policy, False)

    def save(self, resource_speeds=True):
        return super().save(resource_speeds=resource_speeds)


class NonElasticResourcePriority(ABC):
    """
    non_elastic Value policy for the non_elastic task to select the speed
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


class SumSpeedsResourcePriority(NonElasticResourcePriority):
    """sum of speeds"""

    def __init__(self):
        NonElasticResourcePriority.__init__(self, 'Sum speeds')

    def evaluate(self, loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """Calculates the value by summing speeds"""
        return loading_speed + compute_speed + sending_speed


class SumSpeedPowResourcePriority(NonElasticResourcePriority):
    """non_elastic Exp Sum of speeds"""

    def __init__(self):
        NonElasticResourcePriority.__init__(self, 'Exp Sum Speeds')

    def evaluate(self, loading_speed: int, compute_speed: int, sending_speed: int) -> float:
        """Calculate the value by summing the expo of speeds"""
        return loading_speed ** 2 + compute_speed ** 2 + sending_speed ** 2


# TODO add more non_elastic value classes


def generate_non_elastic_tasks(
        tasks: List[ElasticTask], max_tries: int = 5,
        priority: NonElasticResourcePriority = SumSpeedPowResourcePriority()) -> List[NonElasticTask]:
    """
    Generates a list of non_elastic tasks catching if the generation of the task fails for some reasons

    :param tasks: List of tasks
    :param priority: non_elastic allocation priority class
    :param max_tries: The max tries for generated the non_elastic task
    :return: A list of non-elastic tasks
    """
    non_elastic_tasks = []
    for task in tasks:
        tries = 0
        while tries < max_tries:
            try:
                non_elastic_task = NonElasticTask(task, priority)
                non_elastic_tasks.append(non_elastic_task)
                break
            except Exception as e:
                print(e, file=sys.stderr)
                tries += 1
                time.sleep(0.5)
        if tries == max_tries:
            raise Exception(f'Unable to create the non-elastic task {task.__str__()}')
    return non_elastic_tasks
