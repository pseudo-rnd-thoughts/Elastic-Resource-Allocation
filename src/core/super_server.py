"""Super server class"""
from typing import List

from core.server import Server


class SuperServer(Server):
    """Super Server which is the megazord of servers"""

    def __init__(self, servers: List[Server]):
        super().__init__("Super Server",
                         sum(server.storage_capacity for server in servers),
                         sum(server.computation_capacity for server in servers),
                         sum(server.bandwidth_capacity for server in servers))
