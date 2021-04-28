"""task prioritisation functions"""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import exp, sqrt
from random import random, gauss
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from typing import List

    from src.core.task import Task


class TaskPriority(ABC):
    """task prioritisation function class that is inherited with each option"""

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def evaluate(self, task: Task) -> float:
        """task prioritisation function"""
        pass

    @abstractmethod
    def inverse(self, task: Task, density: float) -> float:
        """Inverse of the task prioritisation function for the task value"""
        pass


class ResourceSum(TaskPriority):
    """The sum of a task's required resources"""

    def __init__(self):
        TaskPriority.__init__(self, 'Sum')

    def evaluate(self, task: Task) -> float:
        """task prioritisation function"""
        return task.required_storage + task.required_computation + task.required_results_data

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception('Not supported function of inverse')


class ResourceProduct(TaskPriority):
    """The product of a task's required resources"""

    def __init__(self):
        TaskPriority.__init__(self, 'Product')

    def evaluate(self, task: Task) -> float:
        """task prioritisation function"""
        return task.required_storage * task.required_computation * task.required_results_data

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception('Not supported function of inverse')


class ResourceExpSum(TaskPriority):
    """The sum of exponential of a task's required resources"""

    def __init__(self):
        TaskPriority.__init__(self, 'Exponential Sum')

    def evaluate(self, task: Task) -> float:
        """task prioritisation function"""
        return exp(task.required_storage) + exp(task.required_computation) + exp(task.required_results_data)

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception('Not supported function of inverse')


class ResourceSqrt(TaskPriority):
    """The sum of square root of a task's required resources"""

    def __init__(self, resource_func: TaskPriority = ResourceSum()):
        TaskPriority.__init__(self, f'Sqrt {resource_func.name}')
        self.resource_func = resource_func

    def evaluate(self, task: Task) -> float:
        """task prioritisation"""
        return sqrt(self.resource_func.evaluate(task))

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception('Not supported function of inverse')


class UtilityPerResources(TaskPriority):
    """The utility divided by required resources"""

    def __init__(self, resource_func: TaskPriority = ResourceSum()):
        TaskPriority.__init__(self, f'Utility / {resource_func.name}')
        self.resource_func = resource_func

    def evaluate(self, task: Task) -> float:
        """task prioritisation function"""
        return task.value / self.resource_func.evaluate(task)

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        return density * self.resource_func.evaluate(task)


class DeadlinePerResources(TaskPriority):
    """The deadline divided by required resources"""

    def __init__(self, resource_func: TaskPriority = ResourceSum()):
        TaskPriority.__init__(self, f'Deadline / {resource_func.name}')
        self.resource_func = resource_func

    def evaluate(self, task: Task) -> float:
        """task prioritisation function"""
        return task.deadline / self.resource_func.evaluate(task)

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception('Not supported function of inverse')


class UtilityDeadlinePerResource(TaskPriority):
    """The product of utility and deadline divided by required resources"""

    def __init__(self, resource_func: TaskPriority = ResourceSum()):
        TaskPriority.__init__(self, f'Utility * deadline / {resource_func.name}')
        self.resource_func = resource_func

    def evaluate(self, task: Task) -> float:
        """task prioritisation function"""
        return task.value * task.deadline / self.resource_func.evaluate(task)

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        return density * self.resource_func.evaluate(task) / task.deadline


class UtilityResourcePerDeadline(TaskPriority):
    """The product of utility and deadline divided by required resources"""

    def __init__(self, resource_func: TaskPriority = ResourceSum()):
        TaskPriority.__init__(self, f'Utility * {resource_func.name} / deadline')
        self.resource_func = resource_func

    def evaluate(self, task: Task) -> float:
        """task prioritisation function"""
        return task.value * self.resource_func.evaluate(task) / task.deadline

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        return density * task.deadline / self.resource_func.evaluate(task)


class Random(TaskPriority):
    """Random number generator"""

    def __init__(self):
        TaskPriority.__init__(self, 'Random')

    def evaluate(self, task: Task) -> float:
        """task prioritisation function"""
        return random()

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception('Not supported function of inverse')


class Storage(TaskPriority):
    """Sorted by Storage resource requirement"""

    def __init__(self):
        TaskPriority.__init__(self, 'Storage Requirement')

    def evaluate(self, task: Task) -> float:
        """task prioritisation function"""
        return task.value / task.required_storage

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        return density * task.required_storage


class Value(TaskPriority):
    """Ordered by the value of the tasks alone"""

    def __init__(self):
        TaskPriority.__init__(self, 'Value')

    def evaluate(self, task: Task) -> float:
        """task prioritisation function"""
        return task.value

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        return density


class EvolutionStrategy(TaskPriority):
    """Covariance matrix adaption evolution strategy"""

    def __init__(self, name: int, value_var: Optional[float] = None, deadline_var: Optional[float] = None,
                 storage_var: Optional[float] = None, computational_var: Optional[float] = None,
                 bandwidth_var: Optional[float] = None):
        TaskPriority.__init__(self, f'CMS-ES {name}')

        self.value_var = value_var if value_var else gauss(0, 1)
        self.deadline_var = deadline_var if deadline_var else gauss(0, 1)
        self.storage_var = storage_var if storage_var else gauss(0, 1)
        self.comp_var = computational_var if computational_var else gauss(0, 1)
        self.results_var = bandwidth_var if bandwidth_var else gauss(0, 1)

    def evaluate(self, task: Task) -> float:
        """task prioritisation function"""
        # Todo normally these variables are multiplied together
        return (self.value_var * task.value + self.deadline_var * task.deadline) / \
               (self.storage_var * task.required_storage + self.comp_var * task.required_computation +
                self.results_var * task.required_results_data)

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise NotImplemented('Evolution Strategy for task priority is not implemented yet')


# Functions you actually want to use
policies = [
    Value(),
    UtilityDeadlinePerResource(),
    UtilityDeadlinePerResource(ResourceSqrt())
]

all_policies: List[TaskPriority] = [
    value_density for value_density in [ResourceSum(), ResourceProduct(), ResourceExpSum(), ResourceSqrt()]
]
all_policies += [
    value_density(resource_function)
    for value_density in [UtilityPerResources, UtilityResourcePerDeadline, UtilityDeadlinePerResource]
    for resource_function in [ResourceSum(), ResourceProduct(), ResourceExpSum(), ResourceSqrt()]
]
all_policies += [Storage(), Random(), Value()]

max_name_length = max(len(policy.name) for policy in policies)
