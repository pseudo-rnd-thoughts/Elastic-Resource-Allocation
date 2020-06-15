"""Super server class"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.server import Server

if TYPE_CHECKING:
    from typing import List


class SuperServer(Server):
    """Super Server which is the power rangers megazord of servers"""

    def __init__(self, servers: List[Server]):
        Server.__init__(self, 'Super Server',
                        sum(server.storage_capacity for server in servers),
                        sum(server.computation_capacity for server in servers),
                        sum(server.bandwidth_capacity for server in servers))
