
from __future__ import annotations

from typing import TYPE_CHECKING

from core.core import positive_gaussian_dist
from core.task import Task

if TYPE_CHECKING:
    from typing import Dict, Union


class TaskDistribution(object):
    """
    Random task distribution using gaussian (normal distribution)
    """

    def __init__(self, dist_name, probability,
                 storage_mean, storage_std,
                 computation_mean, computation_std,
                 results_data_mean, results_data_std,
                 value_mean, value_std,
                 deadline_mean, deadline_std):
        self.dist_name = dist_name
        self.probability = probability
        self.storage_mean = storage_mean
        self.storage_std = storage_std
        self.computation_mean = computation_mean
        self.computation_std = computation_std
        self.results_data_mean = results_data_mean
        self.results_data_std = results_data_std
        self.value_mean = value_mean
        self.value_std = value_std
        self.deadline_mean = deadline_mean
        self.deadline_std = deadline_std

    def create_task(self, name) -> Task:
        """
        Creates a new task with name (unique identifier)

        :param name: The name of the task
        :return: A new task object
        """
        task_name = f'{self.dist_name} {name}'
        return Task(name=task_name,
                    required_storage=positive_gaussian_dist(self.storage_mean, self.storage_std),
                    required_computation=positive_gaussian_dist(self.computation_mean, self.computation_std),
                    required_results_data=positive_gaussian_dist(self.results_data_mean, self.results_data_std),
                    value=positive_gaussian_dist(self.value_mean, self.value_std),
                    deadline=int(positive_gaussian_dist(self.deadline_mean, self.deadline_std)))

    def save(self) -> Dict[str, Union[str, int]]:
        """
        Save the task dist

        :return: The Json code for the task dist
        """
        return {
            'name': self.dist_name,
            'probability': self.probability,
            'required_storage_mean': self.storage_mean,
            'required_storage_std': self.storage_std,
            'required_computation_mean': self.computation_mean,
            'required_computation_std': self.computation_std,
            'required_results_data_mean': self.results_data_mean,
            'required_results_data_std': self.results_data_std,
            'value_mean': self.value_mean,
            'value_std': self.value_std,
            'deadline_mean': self.deadline_mean,
            'deadline_std': self.deadline_std
        }
