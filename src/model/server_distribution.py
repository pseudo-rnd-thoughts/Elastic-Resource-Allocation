
from __future__ import annotations

from typing import TYPE_CHECKING

from core.core import positive_gaussian_dist
from core.server import Server

if TYPE_CHECKING:
    from typing import Union, Dict


class ServerDistribution:
    """
    Random server distribution using gaussian (normal distribution)
    """

    def __init__(self, dist_name, probability,
                 storage_mean, storage_std,
                 computation_mean, computation_std,
                 results_data_mean, results_data_std):
        self.dist_name = dist_name
        self.probability = probability
        self.storage_mean = storage_mean
        self.storage_std = storage_std
        self.computation_mean = computation_mean
        self.computation_std = computation_std
        self.results_data_mean = results_data_mean
        self.results_data_std = results_data_std

    def create_server(self, name) -> Server:
        """
        Creates a new server with name (unique identifier)

        :param name: The name of the server
        :return: A new task object
        """
        server_name = f'{self.dist_name} {name}'
        return Server(name=server_name,
                      storage_capacity=positive_gaussian_dist(self.storage_mean, self.storage_std),
                      computation_capacity=positive_gaussian_dist(self.computation_mean, self.computation_std),
                      bandwidth_capacity=positive_gaussian_dist(self.results_data_mean, self.results_data_std))

    def save(self) -> Dict[str, Union[str, int]]:
        """
        Save the server dist

        :return: The Json code for the server dist
        """
        return {
            'name': self.dist_name,
            'probability': self.probability,
            'maximum_storage_mean': self.storage_mean,
            'maximum_storage_std': self.storage_std,
            'maximum_computation_mean': self.computation_mean,
            'maximum_computation_std': self.computation_std,
            'maximum_bandwidth_mean': self.results_data_mean,
            'maximum_bandwidth_std': self.results_data_std
        }
