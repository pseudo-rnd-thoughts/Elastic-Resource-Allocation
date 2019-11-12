"""Branch & Bound algorithm"""

from __future__ import annotations

from auctions.vcg_auction import vcg_auction
from branch_bound.branch_bound import branch_bound_algorithm
from core.core import load_args
from core.model import ModelDist, load_dist, reset_model
from optimal.optimal import optimal_algorithm


def branch_bound_test(model_dist: ModelDist):
    jobs, servers = model_dist.create()
    
    result = branch_bound_algorithm(jobs, servers, debug_update_lower_bound=True)
    print(result.store())

    reset_model(jobs, servers)

    result = optimal_algorithm(jobs, servers, 200)
    print(result.store())


def vcg_testing(model_dist: ModelDist):
    jobs, servers = model_dist.create()

    result = vcg_auction(jobs, servers)
    print()


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])
    
    branch_bound_test(loaded_model_dist)
