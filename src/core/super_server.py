"""Super server class"""

from __future__ import annotations

from typing import List

from src.core.server import Server


class SuperServer(Server):
    """Super Server which is the megazord of servers"""

    def __init__(self, servers: List[Server]):
        super().__init__("Super Server",
                         sum(server.storage_capacity for server in servers),
                         sum(server.computation_capacity for server in servers),
                         sum(server.bandwidth_capacity for server in servers))
