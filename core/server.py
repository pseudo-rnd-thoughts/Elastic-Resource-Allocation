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

    def __init__(self, name: str, max_storage: int, max_computation: int, max_bandwidth: int, price_change: int = 1):
        self.name: str = name
        self.max_storage: int = max_storage
        self.max_computation: int = max_computation
        self.max_bandwidth: int = max_bandwidth
        self.price_change: int = price_change

        # Allocation information
        self.allocated_jobs: List[Job] = []
        self.available_storage: int = max_storage
        self.available_computation: int = max_computation
        self.available_bandwidth: int = max_bandwidth

    def can_run(self, job: Job):
        """
        Checks if a job can be run on a server if it dedicates all of resources to the job
        :param job: The job to test
        """
        return self.available_storage >= job.required_storage \
            and self.available_computation >= 1 \
            and self.available_bandwidth >= 2 and \
            any(job.required_storage * self.available_computation * r +
                s * job.required_computation * r +
                s * self.available_computation * job.required_results_data
                <= job.deadline * s * self.available_computation * r
                for s in range(1, self.available_bandwidth + 1)
                for r in range(1, self.available_bandwidth - s + 1))

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

        self.available_storage = self.max_storage
        self.available_computation = self.max_computation
        self.available_bandwidth = self.max_bandwidth

        self.revenue = 0
        self.value = 0

    def mutate(self, percent) -> Server:
        """
        Mutate the server by a percentage
        :param percent: The percentage to increase the max resources by
        """
        return Server('mutated {}'.format(self.name),
                      int(max(1, self.max_storage - abs(gauss(0, self.max_storage * percent)))),
                      int(max(1, self.max_computation - abs(gauss(0, self.max_computation * percent)))),
                      int(max(1, self.max_bandwidth - abs(gauss(0, self.max_bandwidth * percent)))),
                      self.price_change)


def server_diff(normal_server: Server, mutate_server: Server) -> str:
    """The difference between two severs"""
    return "{}: {}, {}, {}".format(normal_server.name,
                                   normal_server.max_storage - mutate_server.max_storage,
                                   normal_server.max_computation - mutate_server.max_computation,
                                   normal_server.max_bandwidth - mutate_server.max_bandwidth)
