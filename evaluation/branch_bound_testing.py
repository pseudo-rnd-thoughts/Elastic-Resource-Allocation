"""Branch & Bound algorithm"""

from __future__ import annotations

from src.auctions.vcg_auction import vcg_auction
from src.branch_bound.branch_bound import branch_bound_algorithm
from src.core.core import load_args
from src.core.model import ModelDist, load_dist, reset_model
from src.optimal.optimal import optimal_algorithm


def branch_bound_test(model_dist: ModelDist):
    tasks, servers = model_dist.create()
    
    result = branch_bound_algorithm(tasks, servers, debug_update_lower_bound=True)
    print(result.store())

    reset_model(tasks, servers)

    result = optimal_algorithm(tasks, servers, 200)
    print(result.store())


def vcg_testing(model_dist: ModelDist):
    tasks, servers = model_dist.create()

    result = vcg_auction(tasks, servers)
    print()


if __name__ == "__main__":
    args = load_args()

    model_name, task_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, task_dist, args['tasks'], server_dist, args['servers'])
    
    branch_bound_test(loaded_model_dist)
