"""Value Density functions"""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import exp, sqrt
from random import random
from typing import List

from core.job import Job


class ValueDensity(ABC):
    """Value density function class that is inherited with each option"""

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def evaluate(self, job: Job) -> float:
        """Value density function"""
        pass

    @abstractmethod
    def inverse(self, job: Job, density: float) -> float:
        """Inverse of the value density function for the job value"""
        pass


class ResourceSum(ValueDensity):
    """The sum of a job's required resources"""

    def __init__(self):
        super().__init__("Sum")

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return job.required_storage + job.required_computation + job.required_results_data

    def inverse(self, job: Job, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception("Not supported function of inverse")


class ResourceProduct(ValueDensity):
    """The product of a job's required resources"""

    def __init__(self):
        super().__init__("Product")

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return job.required_storage * job.required_computation * job.required_results_data

    def inverse(self, job: Job, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception("Not supported function of inverse")


class ResourceExpSum(ValueDensity):
    """The sum of exponential of a job's required resources"""

    def __init__(self):
        super().__init__("Exponential Sum")

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return exp(job.required_storage) + exp(job.required_computation) + exp(job.required_results_data)

    def inverse(self, job: Job, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception("Not supported function of inverse")


class ResourceSqrt(ValueDensity):
    """The sum of square root of a job's required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        super().__init__("Sqrt {}".format(resource_func.name))
        self.resource_func = resource_func

    def evaluate(self, job: Job) -> float:
        """Value Density"""
        return sqrt(self.resource_func.evaluate(job))

    def inverse(self, job: Job, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception("Not supported function of inverse")


class UtilityPerResources(ValueDensity):
    """The utility divided by required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        super().__init__("Utility / {}".format(resource_func.name))
        self.resource_func = resource_func

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return job.value / self.resource_func.evaluate(job)

    def inverse(self, job: Job, density: float) -> float:
        """Inverse evaluation function"""
        return density * self.resource_func.evaluate(job)


class DeadlinePerResources(ValueDensity):
    """The deadline divided by required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        super().__init__("Deadline / {}".format(resource_func.name))
        self.resource_func = resource_func

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return job.deadline / self.resource_func.evaluate(job)

    def inverse(self, job: Job, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception("Not supported function of inverse")


class UtilityDeadlinePerResource(ValueDensity):
    """The product of utility and deadline divided by required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        super().__init__("Utility * deadline / {}".format(resource_func.name))
        self.resource_func = resource_func

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return job.value * job.deadline / self.resource_func.evaluate(job)

    def inverse(self, job: Job, density: float) -> float:
        """Inverse evaluation function"""
        return density * self.resource_func.evaluate(job) / job.deadline


class UtilityResourcePerDeadline(ValueDensity):
    """The product of utility and deadline divided by required resources"""

    def __init__(self, resource_func: ValueDensity = ResourceSum()):
        super().__init__("Utility * {} / deadline".format(resource_func.name))
        self.resource_func = resource_func

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return job.value * self.resource_func.evaluate(job) / job.deadline

    def inverse(self, job: Job, density: float) -> float:
        """Inverse evaluation function"""
        return density * job.deadline / self.resource_func.evaluate(job)


class Random(ValueDensity):
    """Random number generator"""

    def __init__(self):
        super().__init__("Random")

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return random()

    def inverse(self, job: Job, density: float) -> float:
        """Inverse evaluation function"""
        raise Exception("Not supported function of inverse")


class Storage(ValueDensity):
    """Sorted by Storage resource requirement"""

    def __init__(self):
        super().__init__("Storage Requirement")

    def evaluate(self, job: Job) -> float:
        """Value density function"""
        return job.value / job.required_storage

    def inverse(self, job: Job, density: float) -> float:
        """Inverse evaluation function"""
        return density * job.required_storage


# Functions you actually want to use
policies = [
    UtilityPerResources(),
    UtilityPerResources(ResourceSqrt()),
    UtilityResourcePerDeadline()
]

all_policies: List[ValueDensity] = [
    value_density for value_density in [ResourceSum(), ResourceProduct(), ResourceExpSum(), ResourceSqrt()]
]
all_policies += [
    value_density(resource_function)
    for value_density in [UtilityPerResources, UtilityResourcePerDeadline, UtilityDeadlinePerResource]
    for resource_function in [ResourceSum(), ResourceProduct(), ResourceExpSum(), ResourceSqrt()]
]
all_policies += [Storage(), Random()]

max_name_length = max(len(policy.name) for policy in policies)
