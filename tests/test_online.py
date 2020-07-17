"""
Tests the evaluation online environment works as intended
"""

from __future__ import annotations

from math import ceil
from typing import Iterable

from core.core import reset_model
from core.fixed_task import FixedSumSpeeds, FixedTask
from extra.model import ModelDistribution
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import SumPowPercentage
from greedy.server_selection_policy import SumResources
from greedy.value_density import UtilityDeadlinePerResource, ResourceSqrt
from online import generate_batch_tasks, online_batch_solver, minimal_flexible_optimal_solver
from optimal.fixed_optimal import fixed_optimal_solver


def test_online_model_generation(model_dist=ModelDistribution('models/paper.mdl', num_servers=8),
                                 time_steps: int = 50, batch_lengths: Iterable[int] = (1, 2, 4, 5, 10),
                                 mean_arrival_rate: int = 4, std_arrival_rate: float = 2):
    print()
    tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)

    for batch_length in batch_lengths:
        batched_tasks = generate_batch_tasks(tasks, batch_length, time_steps)
        assert len(batched_tasks) == ceil(time_steps / batch_length)
        assert sum(len(batch_tasks) for batch_tasks in batched_tasks) == len(tasks)
        assert all(0 < task.value for tasks in batched_tasks for task in tasks)
        assert all(task.auction_time <= (batch_num + 1) * batch_length
                   for batch_num, tasks in enumerate(batched_tasks) for task in tasks)
        print(f'Batch lengths: [{", ".join([f"{len(batch_tasks)}" for batch_tasks in batched_tasks])}]')


def test_online_solver(model_dist=ModelDistribution('models/paper.mdl', num_servers=8), time_steps: int = 50,
                       batch_length: int = 3, mean_arrival_rate: int = 4, std_arrival_rate: float = 2):
    print()
    tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
    for server in servers:
        server.storage_capacity = int(server.storage_capacity * 0.3)
        server.computation_capacity = int(server.computation_capacity * 0.3)
        server.bandwidth_capacity = int(server.bandwidth_capacity * 0.3)
    batched_tasks = generate_batch_tasks(tasks, batch_length, time_steps)
    print(f'Tasks per batch time step: [{", ".join([str(len(batch_tasks)) for batch_tasks in batched_tasks])}]')
    result = online_batch_solver(batched_tasks, servers, batch_length, 'Greedy', greedy_algorithm,
                                 value_density=UtilityDeadlinePerResource(ResourceSqrt()),
                                 server_selection_policy=SumResources(),
                                 resource_allocation_policy=SumPowPercentage())
    print(f'Social welfare percentage: {result.percentage_social_welfare}')
    print(result.data)


def test_optimal_solutions(model_dist=ModelDistribution('models/online_paper.mdl', num_servers=8),
                           time_steps: int = 50, mean_arrival_rate: int = 4, std_arrival_rate: float = 2):
    print()
    tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
    fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]

    batched_tasks = generate_batch_tasks(tasks, 1, time_steps)
    optimal_result = online_batch_solver(batched_tasks, servers, 1, 'Online Flexible Optimal',
                                         minimal_flexible_optimal_solver, solver_time_limit=2)
    print(f'Optimal - Social welfare: {optimal_result.social_welfare}')
    reset_model([], servers)

    fixed_batched_tasks = generate_batch_tasks(fixed_tasks, 1, time_steps)
    fixed_optimal_result = online_batch_solver(fixed_batched_tasks, servers, 1, 'Online Fixed Optimal',
                                               fixed_optimal_solver, time_limit=2)
    print(f'Fixed Optimal - Social welfare: {fixed_optimal_result.social_welfare}')
    reset_model([], servers)

    batched_tasks = generate_batch_tasks(tasks, 4, time_steps)
    greedy_result = online_batch_solver(batched_tasks, servers, 4, 'Greedy', greedy_algorithm,
                                        value_density=UtilityDeadlinePerResource(ResourceSqrt()),
                                        server_selection_policy=SumResources(),
                                        resource_allocation_policy=SumPowPercentage())
    print(f'Greedy - Social welfare: {greedy_result.social_welfare}')


def test_batch_lengths(model_dist=ModelDistribution('models/online_paper.mdl', num_servers=8),
                       batch_lengths: Iterable[int] = (1, 5, 10, 15), time_steps: int = 200,
                       mean_arrival_rate: int = 4, std_arrival_rate: float = 2):
    print()
    tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
    original_server_capacities = {server: (server.computation_capacity, server.bandwidth_capacity)
                                  for server in servers}
    results = []
    # Batch greedy algorithm
    for batch_length in batch_lengths:
        batched_tasks = generate_batch_tasks(tasks, batch_length, time_steps)
        flattened_tasks = [task for tasks in batched_tasks for task in tasks]

        # Update the server capacities
        for server in servers:
            server.computation_capacity = original_server_capacities[server][0] * batch_length
            server.bandwidth_capacity = original_server_capacities[server][1] * batch_length

        value_density = UtilityDeadlinePerResource(ResourceSqrt())
        server_selection_policy = SumResources()
        resource_allocation_policy = SumPowPercentage()
        name = f'Greedy {value_density.name}, {server_selection_policy.name}, ' \
               f'{resource_allocation_policy.name}'
        greedy_result = online_batch_solver(batched_tasks, servers, batch_length, name,
                                            greedy_algorithm, value_density=value_density,
                                            server_selection_policy=server_selection_policy,
                                            resource_allocation_policy=resource_allocation_policy)
        results.append(greedy_result)
        print(f'Batch length: {batch_length}, social welfare percent: {greedy_result.percentage_social_welfare}, '
              f'social welfare: {greedy_result.social_welfare}')
        reset_model(flattened_tasks, servers)


def test_caroline_online_models(batch_length: int = 1):
    model_dist = ModelDistribution('models/online_caroline_u4.mdl')
    tasks, servers = model_dist.generate()
    batched_tasks = generate_batch_tasks(tasks, batch_length, 200)
    greedy_result = online_batch_solver(batched_tasks, servers, batch_length, 'Greedy',
                                        greedy_algorithm, value_density=UtilityDeadlinePerResource(ResourceSqrt()),
                                        server_selection_policy=SumResources(),
                                        resource_allocation_policy=SumPowPercentage())
    print(f'\nMean 4 - Social welfare percentage: {greedy_result.percentage_social_welfare}, '
          f'percent tasks allocated: {greedy_result.percentage_tasks_allocated}')

    model_dist = ModelDistribution('models/online_caroline_u7.mdl')
    model_dist.generate()
    batched_tasks = generate_batch_tasks(tasks, batch_length, 200)
    greedy_result = online_batch_solver(batched_tasks, servers, batch_length, 'Greedy',
                                        greedy_algorithm, value_density=UtilityDeadlinePerResource(ResourceSqrt()),
                                        server_selection_policy=SumResources(),
                                        resource_allocation_policy=SumPowPercentage())
    print(f'\nMean 7 - Social welfare percentage: {greedy_result.percentage_social_welfare}, '
          f'percent tasks allocated: {greedy_result.percentage_tasks_allocated}')
