"""
Tests the critical value auction through checking that the critical value is correctly calculated and to test
    for task mutation
"""

from __future__ import annotations

from src.auctions.critical_value_auction import critical_value_auction
from src.core.core import reset_model
from src.extra.model import SyntheticModelDist
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation import SumPercentage
from src.greedy.server_selection import SumResources
from src.greedy.task_priority import UtilityPerResourcesPriority


def test_critical_value(error: float = 0.001):
    """
    To test the critical value action actually returns the critical values

    :param error: To add to the critical value

    1. Run the critical value auction normally
    2. Record the critical values
    3. Repeat the greedy algorithm with each task's value set as critical value if allocated previously
    4. Assert allocation of tasks are equal between critical value auction and greedy algorithm
    """
    print()

    model = SyntheticModelDist(20, 3)
    tasks, servers = model.generate_oneshot()

    print(f'Critical value auction')
    auction_result = critical_value_auction(tasks, servers,
                                            UtilityPerResourcesPriority(), SumResources(), SumPercentage())
    run_tasks = [task for task in tasks if task.running_server]

    for task in run_tasks:
        print(f'\t{task.name} Task - value: {task.value}, critical value: {task.price}')
        original_value = task.value

        reset_model(tasks, servers, forget_prices=False)
        task.value = task.price + error
        greedy_result = greedy_algorithm(tasks, servers,
                                         UtilityPerResourcesPriority(), SumResources(), SumPercentage())
        assert auction_result.social_welfare == greedy_result.social_welfare and task.running_server is not None

        if 0 < task.price:
            reset_model(tasks, servers, forget_prices=False)
            task.value = task.price - error
            greedy_result = greedy_algorithm(tasks, servers,
                                             UtilityPerResourcesPriority(), SumResources(), SumPercentage())
            assert greedy_result.social_welfare < auction_result.social_welfare and task.running_server is None

        task.value = original_value
