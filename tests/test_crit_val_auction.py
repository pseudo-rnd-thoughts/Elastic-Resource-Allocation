
from __future__ import annotations

from auctions.critical_value_auction import critical_value_auction
from core.core import reset_model
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import SumPercentage
from greedy.server_selection_policy import SumResources
from greedy.value_density import UtilityPerResources
from model.model_distribution import load_model_distribution, ModelDistribution


def test_critical_value(error: float = 0.1):
    """
    To test the critical value action actually returns the critical values

    :param error: To add to the critical value

    1. Run the critical value auction normally
    2. Record the critical values
    3. Repeat the greedy algorithm with each task's value set as critical value if allocated previously
    4. Assert allocation of tasks are equal between critical value auction and greedy algorithm
    """
    print()

    distribution_name, task_distributions, server_distributions = load_model_distribution('models/basic.mdl')
    model = ModelDistribution(distribution_name, task_distributions, 20, server_distributions, 3)

    tasks, servers = model.create()

    auction_result = critical_value_auction(tasks, servers, UtilityPerResources(), SumResources(), SumPercentage())

    for task in tasks:
        if 0 < task.price:
            reset_model(tasks, servers, forgot_price=False)

            original_value = task.value
            task.value = task.price + error
            greedy_result = greedy_algorithm(tasks, servers, UtilityPerResources(), SumResources(), SumPercentage())

            assert task.running_server is not None

            task.value = original_value
