"""Super server class"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.server import Server

if TYPE_CHECKING:
    from typing import List


class SuperServer(Server):
    """Super Server which is the power rangers megazord of servers"""

    def __init__(self, servers: List[Server]):
        price_changes = [server.price_change for server in servers]
        initial_prices = [server.initial_price for server in servers]
        Server.__init__(self, 'Super Server',
                        storage_capacity=sum(server.storage_capacity for server in servers),
                        computation_capacity=sum(server.computation_capacity for server in servers),
                        bandwidth_capacity=sum(server.bandwidth_capacity for server in servers),
                        price_change=max(set(price_changes), key=price_changes.count),
                        initial_price=max(set(initial_prices), key=initial_prices.count))
