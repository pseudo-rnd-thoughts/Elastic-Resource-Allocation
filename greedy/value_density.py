"""Value Density functions"""

from __future__ import annotations
from abc import ABC, abstractmethod
from math import exp, sqrt
from random import random

from core.job import Job


class ValueDensity(ABC):
    """Value density function class that is inherited with each option"""

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def evaluate(self, job: Job) -> float:
        """Value density function"""
        pass


class ResourceSum(ValueDensity):
    """The sum of a job's required resources"""

    def __init__(self):
        super().__init__("Sum")

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return job.required_storage + job.required_computation + job.required_results_data


class ResourceProduct(ValueDensity):
    """The product of a job's required resources"""

    def __init__(self):
        super().__init__("Product")

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return job.required_storage * job.required_computation * job.required_results_data


class ResourceExpSum(ValueDensity):
    """The sum of exponential of a job's required resources"""

    def __init__(self):
        super().__init__("Exponential Sum")

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return exp(job.required_storage) + exp(job.required_computation) + exp(job.required_results_data)


class ResourceSqrt(ValueDensity):
    """The sum of square root of a job's required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        super().__init__("Sqrt {}".format(resource_func.name))
        self.resource_func = resource_func

    def evaluate(self, job: Job) -> float:
        """Value Density"""
        return sqrt(self.resource_func.evaluate(job))


class UtilityPerResources(ValueDensity):
    """The utility divided by required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        super().__init__("Utility / {}".format(resource_func.name))
        self.resource_func = resource_func

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return job.utility / self.resource_func.evaluate(job)


class DeadlinePerResources(ValueDensity):
    """The deadline divided by required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        super().__init__("Deadline / {}".format(resource_func.name))
        self.resource_func = resource_func

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return job.deadline / self.resource_func.evaluate(job)


class UtilityDeadlinePerResource(ValueDensity):
    """The product of utility and deadline divided by required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        super().__init__("Utility * deadline / {}".format(resource_func.name))
        self.resource_func = resource_func

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return job.utility * job.deadline / self.resource_func.evaluate(job)


class Random(ValueDensity):
    """Random number generator"""

    def __init__(self):
        super().__init__("Random")

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return random()


# Functions you actually want to use
policies = (
    UtilityPerResources(),
    UtilityDeadlinePerResource(),
    UtilityPerResources(ResourceSqrt())
)

max_name_length = max(len(policy.name) for policy in policies)
