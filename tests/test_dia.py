"""
Tests the decentralised iterative auction
"""

from __future__ import annotations

from auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction, \
    greedy_decentralised_iterative_auction, PriceResourcePerDeadline
from core.core import reset_model
from greedy.resource_allocation_policy import SumPercentage
from model.model_distribution import load_model_distribution, ModelDistribution


def test_optimal_dia():
    print()
    distribution_name, task_distributions, server_distributions = load_model_distribution('models/basic.mdl')
    model = ModelDistribution(distribution_name, task_distributions, 20, server_distributions, 3)

    tasks, servers = model.create()

    result = optimal_decentralised_iterative_auction(tasks, servers, time_limit=1, debug_allocation=True)
    result.pretty_print()


def test_greedy_dia():
    print()
    distribution_name, task_distributions, server_distributions = load_model_distribution('models/basic.mdl')
    model = ModelDistribution(distribution_name, task_distributions, 20, server_distributions, 3)

    tasks, servers = model.create()

    result = greedy_decentralised_iterative_auction(tasks, servers,
                                                    PriceResourcePerDeadline(), SumPercentage(), debug_allocation=True)
    result.pretty_print()


def test_optimal_greedy_dia(repeats: int = 5):
    print()
    distribution_name, task_distributions, server_distributions = load_model_distribution('models/basic.mdl')
    model = ModelDistribution(distribution_name, task_distributions, 20, server_distributions, 3)

    print(f' Optimal    | Greedy')
    print(f'Time  | SW  | Time  | SW')
    for repeat in range(repeats):
        tasks, servers = model.create()

        optimal_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit=1)

        reset_model(tasks, servers)
        greedy_result = greedy_decentralised_iterative_auction(tasks, servers, PriceResourcePerDeadline(),
                                                               SumPercentage())

        print(f'{optimal_result.solve_time} | {optimal_result.social_welfare} | '
              f'{greedy_result.solve_time} | {greedy_result.social_welfare}')
