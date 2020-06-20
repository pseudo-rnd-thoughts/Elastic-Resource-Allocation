"""Branch & Bound algorithm"""

from __future__ import annotations

from auctions.vcg_auction import vcg_auction
from branch_bound.branch_bound import branch_bound_algorithm
from core.core import reset_model
from extra.io import load_args
from extra.model import ModelDistribution
from optimal.optimal import optimal_algorithm


def branch_bound_test(model_dist: ModelDistribution):
    """
    Branch and bound test

    :param model_dist: Model distribution
    """
    tasks, servers = model_dist.generate()

    result = branch_bound_algorithm(tasks, servers, debug_update_lower_bound=True)
    print(result.pretty_print())

    reset_model(tasks, servers)

    result = optimal_algorithm(tasks, servers, 200)
    print(result.pretty_print())


def vcg_testing(model_dist: ModelDistribution):
    """
    VCG testing

    :param model_dist: Model distribution
    """
    tasks, servers = model_dist.generate()

    result = vcg_auction(tasks, servers)
    print(result.pretty_print())


if __name__ == "__main__":
    args = load_args()
    loaded_model_dist = ModelDistribution(args['model'], args['tasks'], args['servers'])
    branch_bound_test(loaded_model_dist)
