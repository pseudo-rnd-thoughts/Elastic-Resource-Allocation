"""Job object implementation"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.server import Server


class Job(object):
    """
    Job object with name and required resources to use (storage, computation and models data)
    When the job is allocated to a server then the resources speed and server are set

    Constructor arguments are final as they dont need changing after initialisation
    """

    # Allocation information
    loading_speed: int = 0
    compute_speed: int = 0
    sending_speed: int = 0
    running_server: Optional[Server] = None

    price: float = 0  # This is for auctions only

    def __init__(self, name: str, required_storage: int, required_computation: int, required_results_data: int,
                 value: float, deadline: int):
        self.name: str = name
        self.required_storage: int = required_storage
        self.required_computation: int = required_computation
        self.required_results_data: int = required_results_data
        self.value: float = value
        self.deadline: int = deadline

    def allocate(self, loading_speed: int, compute_speed: int, sending_speed: int, running_server: Server,
                 price: float = 0):
        """
        Sets the job attribute for when it is allocated to a server
        :param loading_speed: The loading speed of the job
        :param compute_speed: The computational speed of the job
        :param sending_speed: The sending speed of the jobs
        :param running_server: The server the job is running on
        :param price: The price of the job
        """
        assert loading_speed > 0 and compute_speed > 0 and sending_speed > 0,\
            "Job {} with loading {} compute {} sending {}"\
            .format(self.name, loading_speed, compute_speed, sending_speed)
        # Python floats are overflowing causing errors, e.g. 2/3 + 1/3 != 1 in python but is with cplex
        assert self.required_storage * compute_speed * sending_speed + \
            loading_speed * self.required_computation * sending_speed + \
            loading_speed * compute_speed * self.required_results_data <= \
            self.deadline * loading_speed * compute_speed * sending_speed

        self.loading_speed = loading_speed
        self.compute_speed = compute_speed
        self.sending_speed = sending_speed
        self.running_server = running_server

        self.price = price

    def reset_allocation(self):
        """
        Resets the allocation data to the default
        """
        self.loading_speed = 0
        self.compute_speed = 0
        self.sending_speed = 0
        self.running_server = None
        
    def utility(self):
        """
        The social welfare of the job
        :return: The job value minus job price
        """
        return self.value - self.price
