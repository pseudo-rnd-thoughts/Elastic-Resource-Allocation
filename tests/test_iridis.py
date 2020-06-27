"""
Tests if Iridis works with the code
"""

from auctions.critical_value_auction import critical_value_auction
from auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction
from auctions.vcg_auction import vcg_auction, fixed_vcg_auction
from core.core import reset_model
from core.fixed_task import FixedTask, FixedSumPowerSpeeds
from extra.model import ModelDistribution
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import SumPercentage
from greedy.server_selection_policy import SumResources
from greedy.value_density import UtilityPerResources
from optimal.fixed_optimal import fixed_optimal
from optimal.flexible_optimal import flexible_optimal


def main():
    """
    Runs the main script for testing iridis
    """
    model = ModelDistribution('models/basic.mdl', 20, 3)
    tasks, servers = model.generate()
    fixed_tasks = [FixedTask(task, FixedSumPowerSpeeds()) for task in tasks]

    optimal_result = flexible_optimal(tasks, servers)
    optimal_result.pretty_print()

    reset_model(tasks, servers)
    fixed_optimal_result = fixed_optimal(fixed_tasks, servers)
    fixed_optimal_result.pretty_print()

    reset_model(fixed_tasks, servers)
    greedy_results = greedy_algorithm(tasks, servers, UtilityPerResources(), SumResources(), SumPercentage())
    greedy_results.pretty_print()

    reset_model(tasks, servers)
    critical_value_results = critical_value_auction(tasks, servers, UtilityPerResources(), SumResources(), SumPercentage())
    critical_value_results.pretty_print()

    reset_model(tasks, servers)
    optimal_dia_results = optimal_decentralised_iterative_auction(tasks, servers, time_limit=1)
    optimal_dia_results.pretty_print()

    reset_model(tasks, servers)
    vcg_result = vcg_auction(tasks, servers, time_limit=10)
    vcg_result.pretty_print()

    reset_model(tasks, servers)
    fixed_vcg_result = fixed_vcg_auction(fixed_tasks, servers, time_limit=10)
    fixed_vcg_result.pretty_print()


if __name__ == "__main__":
    main()
