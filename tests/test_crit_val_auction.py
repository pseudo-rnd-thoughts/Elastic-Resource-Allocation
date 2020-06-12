
from __future__ import annotations

from auctions.critical_value_auction import critical_value_auction
from core.core import reset_model
from greedy.resource_allocation_policy import SumPercentage
from greedy.server_selection_policy import SumResources
from greedy.value_density import UtilityPerResources
from model.model_distribution import load_model_distribution, ModelDistribution


def test_critical_value():
    """
    To test the critical value action actually returns the critical values

    1. Run the critical value auction normally
    2. Record the critical values
    3. Repeat the critical value auction with each task's value set as critical value if allocated previously
    4. Assert that the price of the task is equal to the critical value from the auction
    """

    distribution_name, task_distributions, server_distributions = load_model_distribution('tests/test.mdl')
    model = ModelDistribution(distribution_name, task_distributions, 20, server_distributions, 3)

    tasks, servers = model.create()
    results = critical_value_auction(tasks, servers, UtilityPerResources(), SumResources(), SumPercentage())

    critical_values = {task: task.price for task in tasks}
    for task in tasks:
        task.value = task.price
    reset_model(tasks, servers)

    results = critical_value_auction(tasks, servers, UtilityPerResources(), SumResources(), SumPercentage())
    assert all(task.price == critical_values[task] for task in tasks)

