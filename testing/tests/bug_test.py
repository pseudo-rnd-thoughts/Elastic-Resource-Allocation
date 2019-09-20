"""Bug testing"""

from __future__ import annotations

from core.core import load_args
from core.model import ModelDist, load_dist

from auctions.fixed_vcg_auction import fixed_vcg_auction
from auctions.decentralised_iterative_auction import decentralised_iterative_auction


def run_fixed_auction(model_dist: ModelDist):
    jobs, servers = model_dist.create()
    result = fixed_vcg_auction(jobs, servers, 15, True, True)
    print(result.store())


def run_decentralised_iterative_auction(model_dist: ModelDist):
    jobs, servers = model_dist.create()
    result = decentralised_iterative_auction(jobs, servers, 15, lambda x: 20, True, True)
    print(result.store())


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])

    # run_fixed_auction(loaded_model_dist)
    run_decentralised_iterative_auction(loaded_model_dist)
