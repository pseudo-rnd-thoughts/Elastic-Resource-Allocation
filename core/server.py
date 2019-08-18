"""Server object implementation"""

from __future__ import annotations
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.job import Job


class Server(object):
    """
    Server object with a name and resources allocated
    """

    revenue: float = 0  # This is the total price of the jobs allocated

    def __init__(self, name: str, max_storage: int, max_computation: int, max_bandwidth: int):
        self.name: str = name
        self.max_storage: int = max_storage
        self.max_computation: int = max_computation
        self.max_bandwidth: int = max_bandwidth

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
        return self.available_storage >= job.required_storage and self.available_computation >= 1 \
            and self.available_bandwidth >= 2 and any(job.required_storage / s + job.required_computation / w +
                                                      job.required_results_data / r <= job.deadline
                                                      for s in range(1, self.available_bandwidth + 1)
                                                      for w in range(1, self.available_computation + 1)
                                                      for r in range(1, self.available_bandwidth - s + 1))

    def allocate_job(self, job: Job):
        """
        Updates the server attributes for when it is allocated within jobs
        :param job: The job being allocated
        """
        assert job.loading_speed > 0 and job.compute_speed > 0 and job.sending_speed > 0
        assert self.available_storage >= job.required_storage
        assert self.available_computation >= job.compute_speed
        assert self.available_bandwidth >= job.loading_speed + job.sending_speed

        self.allocated_jobs.append(job)
        self.available_storage -= job.required_storage
        self.available_computation -= job.compute_speed
        self.available_bandwidth -= job.loading_speed + job.sending_speed

        self.revenue += job.price

    def reset_allocations(self):
        """
        Resets the allocation information
        """
        self.allocated_jobs = []
        self.available_storage = self.max_storage
        self.available_computation = self.max_computation
        self.available_bandwidth = self.max_bandwidth

        self.revenue = 0
