"""Server object implementation"""

from __future__ import annotations

from random import gauss
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.job import Job


class Server(object):
    """
    Server object with a name and resources allocated
    """

    revenue: float = 0  # This is the total price of the job's allocated
    value: float = 0  # This is the total value of the job's allocated

    def __init__(self, name: str, storage_capacity: int, computation_capacity: int, bandwidth_capacity: int,
                 price_change: int = 1):
        self.name: str = name
        self.storage_capacity: int = storage_capacity
        self.computation_capacity: int = computation_capacity
        self.bandwidth_capacity: int = bandwidth_capacity
        self.price_change: int = price_change

        # Allocation information
        self.allocated_jobs: List[Job] = []
        self.available_storage: int = storage_capacity
        self.available_computation: int = computation_capacity
        self.available_bandwidth: int = bandwidth_capacity

    # noinspection DuplicatedCode
    def can_run(self, job: Job) -> bool:
        """
        Checks if a job can be run on a server if it dedicates all of it's available resources to the job
        :param job: The job to test
        :return: If it can run
        """

        """
        Old code
        
        return self.available_storage >= job.required_storage \
            and self.available_computation >= 1 \
            and self.available_bandwidth >= 2 and \
            any(job.required_storage * self.available_computation * r +
                s * job.required_computation * r +
                s * self.available_computation * job.required_results_data
                <= job.deadline * s * self.available_computation * r
                for s in range(1, self.available_bandwidth + 1)
                for r in range(1, self.available_bandwidth - s + 1))
                
        if self.available_bandwidth < 2 or self.available_computation < 1:
            return False

        model = CpoModel("CanRun")
        loading_speed = model.integer_var(min=1, max=self.available_bandwidth - 1)
        compute_speed = model.integer_var(min=1, max=self.available_computation)
        sending_speed = model.integer_var(min=1, max=self.available_bandwidth - 1)

        model.add(job.required_storage / loading_speed +
                  job.required_computation / compute_speed +
                  job.required_results_data / sending_speed <= job.deadline)
        model.add(job.required_storage <= self.available_storage)
        model.add(loading_speed + sending_speed <= self.available_bandwidth)

        model_solution = model.solve(log_output=None)

        return model_solution.get_solve_status() == SOLVE_STATUS_FEASIBLE
        """
        if job.required_storage > self.available_storage or \
                self.available_bandwidth < 2 or \
                self.available_computation < 1:
            return False

        for s in range(1, self.available_bandwidth):
            if job.required_storage * self.available_computation * (self.available_bandwidth - s) + \
                    s * job.required_computation * (self.available_bandwidth - s) +\
                    s * self.available_computation * job.required_results_data <= \
                    job.deadline * s * self.available_computation * (self.available_bandwidth - s):
                return True
        return False

    # noinspection DuplicatedCode
    def can_empty_run(self, job: Job) -> bool:
        """
        Checks if a job can be run on a server if it dedicates all of it's possible resources to the job
        :param job: The job to test
        :return: If it can run
        """

        """
        Old code
        return self.storage_capacity >= job.required_storage \
            and self.computation_capacity >= 1 \
            and self.bandwidth_capacity >= 2 and \
            any(job.required_storage * self.computation_capacity * r +
                s * job.required_computation * r +
                s * self.computation_capacity * job.required_results_data
                <= job.deadline * s * self.available_computation * r
                for s in range(1, self.bandwidth_capacity + 1)
                for r in range(1, self.bandwidth_capacity - s + 1))
                
        if self.bandwidth_capacity < 2 or self.computation_capacity < 1:
            return False

        model = CpoModel("CanRunEmpty")
        loading_speed = model.integer_var(min=1, max=self.bandwidth_capacity - 1)
        compute_speed = model.integer_var(min=1, max=self.computation_capacity)
        sending_speed = model.integer_var(min=1, max=self.bandwidth_capacity - 1)

        model.add(job.required_storage / loading_speed +
                  job.required_computation / compute_speed +
                  job.required_results_data / sending_speed <= job.deadline)
        model.add(job.required_storage <= self.storage_capacity)
        model.add(loading_speed + sending_speed <= self.bandwidth_capacity)

        model_solution = model.solve(log_output=None)

        return model_solution.get_solve_status() == SOLVE_STATUS_FEASIBLE
        """

        if job.required_storage > self.storage_capacity or \
                self.bandwidth_capacity < 2 or \
                self.computation_capacity < 1:
            return False

        for s in range(1, self.bandwidth_capacity):
            if job.required_storage * self.computation_capacity * (self.bandwidth_capacity - s) + \
                    s * job.required_computation * (self.bandwidth_capacity - s) +\
                    s * self.computation_capacity * job.required_results_data <= \
                    job.deadline * s * self.computation_capacity * (self.bandwidth_capacity - s):
                return True
        return False

    def allocate_job(self, job: Job):
        """
        Updates the server attributes for when it is allocated within jobs
        :param job: The job being allocated
        """
        assert job.loading_speed > 0 and job.compute_speed > 0 and job.sending_speed > 0, \
            "Job {} - loading: {}, compute: {}, sending: {}"\
            .format(job.name, job.loading_speed, job.compute_speed, job.sending_speed)
        assert self.available_storage >= job.required_storage, \
            "Server {} available storage {}, job required storage {}"\
            .format(self.name, self.available_storage, job.required_storage)
        assert self.available_computation >= job.compute_speed, \
            "Server {} available computation {}, job compute speed {}"\
            .format(self.name, self.available_computation, job.compute_speed)
        assert self.available_bandwidth >= job.loading_speed + job.sending_speed, \
            "Server {} available bandwidth {}, job loading speed {} and sending speed {}"\
            .format(self.name, self.available_bandwidth, job.loading_speed, job.sending_speed)
        assert job not in self.allocated_jobs, "Job {} is already allocated to the server {}"\
            .format(job.name, self.name)

        self.allocated_jobs.append(job)
        self.available_storage -= job.required_storage
        self.available_computation -= job.compute_speed
        self.available_bandwidth -= (job.loading_speed + job.sending_speed)

        self.revenue += job.price
        self.value += job.value

    def reset_allocations(self):
        """
        Resets the allocation information
        """
        self.allocated_jobs = []

        self.available_storage = self.storage_capacity
        self.available_computation = self.computation_capacity
        self.available_bandwidth = self.bandwidth_capacity

        self.revenue = 0
        self.value = 0

    def mutate(self, percent) -> Server:
        """
        Mutate the server by a percentage
        :param percent: The percentage to increase the max resources by
        """
        return Server('mutated {}'.format(self.name),
                      int(max(1, self.storage_capacity - abs(gauss(0, self.storage_capacity * percent)))),
                      int(max(1, self.computation_capacity - abs(gauss(0, self.computation_capacity * percent)))),
                      int(max(1, self.bandwidth_capacity - abs(gauss(0, self.bandwidth_capacity * percent)))),
                      self.price_change)


def server_diff(normal_server: Server, mutate_server: Server) -> str:
    """The difference between two severs"""
    return "{}: {}, {}, {}".format(normal_server.name,
                                   normal_server.storage_capacity - mutate_server.storage_capacity,
                                   normal_server.computation_capacity - mutate_server.computation_capacity,
                                   normal_server.bandwidth_capacity - mutate_server.bandwidth_capacity)
