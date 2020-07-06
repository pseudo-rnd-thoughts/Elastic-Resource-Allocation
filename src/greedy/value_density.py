"""Value Density functions"""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import exp, sqrt
from random import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List

    from src.core.task import Task


class ValueDensity(ABC):
    """Value density function class that is inherited with each option"""

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def evaluate(self, task: Task) -> float:
        """Value density function"""
        pass

    @abstractmethod
    def inverse(self, task: Task, density: float) -> float:
        """Inverse of the value density function for the task value"""
        pass


class ResourceSum(ValueDensity):
    """The sum of a task's required resources"""

    def __init__(self):
        ValueDensity.__init__(self, 'Sum')

    def evaluate(self, task: Task) -> float:
        """Value density function"""
        return task.required_storage + task.required_computation + task.required_results_data

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception('Not supported function of inverse')


class ResourceProduct(ValueDensity):
    """The product of a task's required resources"""

    def __init__(self):
        ValueDensity.__init__(self, 'Product')

    def evaluate(self, task: Task) -> float:
        """Value density function"""
        return task.required_storage * task.required_computation * task.required_results_data

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception('Not supported function of inverse')


class ResourceExpSum(ValueDensity):
    """The sum of exponential of a task's required resources"""

    def __init__(self):
        ValueDensity.__init__(self, 'Exponential Sum')

    def evaluate(self, task: Task) -> float:
        """Value density function"""
        return exp(task.required_storage) + exp(task.required_computation) + exp(task.required_results_data)

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception('Not supported function of inverse')


class ResourceSqrt(ValueDensity):
    """The sum of square root of a task's required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        ValueDensity.__init__(self, f'Sqrt {resource_func.name}')
        self.resource_func = resource_func

    def evaluate(self, task: Task) -> float:
        """Value Density"""
        return sqrt(self.resource_func.evaluate(task))

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception('Not supported function of inverse')


class UtilityPerResources(ValueDensity):
    """The utility divided by required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        ValueDensity.__init__(self, f'Utility / {resource_func.name}')
        self.resource_func = resource_func

    def evaluate(self, task: Task) -> float:
        """Value density function"""
        return task.value / self.resource_func.evaluate(task)

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        return density * self.resource_func.evaluate(task)


class DeadlinePerResources(ValueDensity):
    """The deadline divided by required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        ValueDensity.__init__(self, f'Deadline / {resource_func.name}')
        self.resource_func = resource_func

    def evaluate(self, task: Task) -> float:
        """Value density function"""
        return task.deadline / self.resource_func.evaluate(task)

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception('Not supported function of inverse')


class UtilityDeadlinePerResource(ValueDensity):
    """The product of utility and deadline divided by required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        ValueDensity.__init__(self, f'Utility * deadline / {resource_func.name}')
        self.resource_func = resource_func

    def evaluate(self, task: Task) -> float:
        """Value density function"""
        return task.value * task.deadline / self.resource_func.evaluate(task)

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        return density * self.resource_func.evaluate(task) / task.deadline


class UtilityResourcePerDeadline(ValueDensity):
    """The product of utility and deadline divided by required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        ValueDensity.__init__(self, f'Utility * {resource_func.name} / deadline')
        self.resource_func = resource_func

    def evaluate(self, task: Task) -> float:
        """Value density function"""
        return task.value * self.resource_func.evaluate(task) / task.deadline

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        return density * task.deadline / self.resource_func.evaluate(task)


class Random(ValueDensity):
    """Random number generator"""

    def __init__(self):
        ValueDensity.__init__(self, 'Random')

    def evaluate(self, task: Task) -> float:
        """Value density function"""
        return random()

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception('Not supported function of inverse')


class Storage(ValueDensity):
    """Sorted by Storage resource requirement"""

    def __init__(self):
        ValueDensity.__init__(self, 'Storage Requirement')

    def evaluate(self, task: Task) -> float:
        """Value density function"""
        return task.value / task.required_storage

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        return density * task.required_storage


class Value(ValueDensity):
    """Ordered by the value of the tasks alone"""

    def __init__(self):
        ValueDensity.__init__(self, 'Value')

    def evaluate(self, task: Task) -> float:
        """Value density function"""
        return task.value

    def inverse(self, task: Task, density: float) -> float:
        """Inverse evaluation function"""
        return density


# Functions you actually want to use
policies = [
    UtilityPerResources(ResourceSqrt()),
    UtilityResourcePerDeadline(),
    UtilityResourcePerDeadline(ResourceSqrt())
]

all_policies: List[ValueDensity] = [
    value_density for value_density in [ResourceSum(), ResourceProduct(), ResourceExpSum(), ResourceSqrt()]
]
all_policies += [
    value_density(resource_function)
    for value_density in [UtilityPerResources, UtilityResourcePerDeadline, UtilityDeadlinePerResource]
    for resource_function in [ResourceSum(), ResourceProduct(), ResourceExpSum(), ResourceSqrt()]
]
all_policies += [Storage(), Random(), Value()]

max_name_length = max(len(policy.name) for policy in policies)
