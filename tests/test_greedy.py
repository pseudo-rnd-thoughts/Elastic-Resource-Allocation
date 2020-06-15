
from __future__ import annotations

from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import SumPercentage
from greedy.server_selection_policy import SumResources
from greedy.value_density import UtilityPerResources
from model.model_distribution import load_model_distribution, ModelDistribution


def test_greedy_algo():
    distribution_name, task_distributions, server_distributions = load_model_distribution('tests/test.mdl')
    model = ModelDistribution(distribution_name, task_distributions, 20, server_distributions, 3)

    tasks, servers = model.create()
    results = greedy_algorithm(tasks, servers, UtilityPerResources(), SumResources(), SumPercentage())
