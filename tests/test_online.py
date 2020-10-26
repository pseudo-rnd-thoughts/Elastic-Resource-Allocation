"""
Tests the evaluation online environment works as intended
"""

from __future__ import annotations

from math import ceil
from typing import Iterable, List

from core.core import reset_model
from core.fixed_task import FixedTask, SumSpeedPowsFixedPolicy
from core.server import Server
from core.task import Task
from extra.model import ModelDistribution
from extra.visualise import minimise_resource_allocation
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import SumPowPercentage
from greedy.server_selection_policy import SumResources
from greedy.task_prioritisation import UtilityDeadlinePerResource, ResourceSqrt
from online import generate_batch_tasks, online_batch_solver
from optimal.fixed_optimal import fixed_optimal_solver
from optimal.flexible_optimal import flexible_optimal_solver


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


def test_online_server_capacities(model_dist=ModelDistribution('models/paper.mdl', num_servers=8), time_steps: int = 50,
                                  batch_length: int = 3, mean_arrival_rate: int = 4, std_arrival_rate: float = 2,
                                  capacities: float = 0.3):
    print()
    tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
    for server in servers:
        server.storage_capacity = int(server.storage_capacity * capacities)
        server.computation_capacity = int(server.computation_capacity * capacities)
        server.bandwidth_capacity = int(server.bandwidth_capacity * capacities)
    batched_tasks = generate_batch_tasks(tasks, batch_length, time_steps)
    print(f'Tasks per batch time step: [{", ".join([str(len(batch_tasks)) for batch_tasks in batched_tasks])}]')
    result = online_batch_solver(batched_tasks, servers, batch_length, 'Greedy', greedy_algorithm,
                                 value_density=UtilityDeadlinePerResource(ResourceSqrt()),
                                 server_selection_policy=SumResources(),
                                 resource_allocation_policy=SumPowPercentage())
    print(f'Social welfare percentage: {result.percentage_social_welfare}')
    print(result.data)


def test_optimal_solutions(model_dist=ModelDistribution('models/online_paper.mdl', num_servers=8),
                           time_steps: int = 20, mean_arrival_rate: int = 4, std_arrival_rate: float = 2):
    tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
    fixed_tasks = [FixedTask(task, SumSpeedPowsFixedPolicy()) for task in tasks]

    # batched_tasks = generate_batch_tasks(tasks, 1, time_steps)
    # optimal_result = online_batch_solver(batched_tasks, servers, 1, 'Online Flexible Optimal',
    #                                      minimal_flexible_optimal_solver, solver_time_limit=2)
    # print(f'Optimal - Social welfare: {optimal_result.social_welfare}')
    # reset_model([], servers)

    fixed_batched_tasks = generate_batch_tasks(fixed_tasks, 1, time_steps)
    fixed_optimal_result = online_batch_solver(fixed_batched_tasks, servers, 1, 'Fixed Optimal',
                                               fixed_optimal_solver, time_limit=2)
    print(f'\nFixed Optimal - Social welfare: {fixed_optimal_result.social_welfare}')
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


def test_online_fixed_task():
    model_dist = ModelDistribution('models/online_paper.mdl', num_servers=8)
    tasks, servers = model_dist.generate_online(20, 4, 2)
    fixed_tasks = [FixedTask(task, SumSpeedPowsFixedPolicy()) for task in tasks]
    batched_fixed_tasks = generate_batch_tasks(fixed_tasks, 5, 20)

    for batch_fixed_tasks in batched_fixed_tasks:
        for fixed_task in batch_fixed_tasks:
            time_taken = fixed_task.required_storage * fixed_task.compute_speed * fixed_task.sending_speed + \
                         fixed_task.loading_speed * fixed_task.required_computation * fixed_task.sending_speed + \
                         fixed_task.loading_speed * fixed_task.compute_speed * fixed_task.required_results_data
            assert time_taken <= fixed_task.deadline * fixed_task.loading_speed * \
                   fixed_task.compute_speed * fixed_task.sending_speed


def test_minimise_resources():
    model_dist = ModelDistribution('models/online_paper.mdl', num_servers=8)
    tasks, servers = model_dist.generate_online(20, 4, 2)

    def custom_solver(_tasks: List[Task], _servers: List[Server],
                      solver_time_limit: int = 3, minimise_time_limit: int = 2):
        valid_servers = [server for server in servers if
                         1 <= server.available_computation and 1 <= server.available_bandwidth]
        server_availability = {server: (server.available_computation, server.available_bandwidth) for server in servers}
        flexible_optimal_solver(_tasks, valid_servers, solver_time_limit)

        for server, (compute_availability, bandwidth_availability) in server_availability.items():
            server_old_tasks = [task for task in server.allocated_tasks if task not in _tasks]
            max_bandwidth = server.bandwidth_capacity - sum(
                task.loading_speed + task.sending_speed for task in server_old_tasks)
            max_computation = server.computation_capacity - sum(task.compute_speed for task in server_old_tasks)
            assert compute_availability == max_computation, f'Availability: {compute_availability}, actual: {max_computation}'
            assert bandwidth_availability == max_bandwidth, f'Availability: {bandwidth_availability}, actual: {max_bandwidth}'

        minimise_resource_allocation(_tasks, valid_servers, minimise_time_limit)

    batched_tasks = generate_batch_tasks(tasks, 1, 20)
    optimal_result = online_batch_solver(batched_tasks, servers, 1, 'Online Flexible Optimal',
                                         custom_solver, solver_time_limit=2)
    print(f'Optimal - Social welfare: {optimal_result.social_welfare}')
    reset_model([], servers)


def test_batch_length(model_dist=ModelDistribution('models/online_paper.mdl', num_servers=8), batch_lengths=(1, 2, 3),
                      time_steps: int = 20, mean_arrival_rate: int = 4, std_arrival_rate: float = 2):
    print('')
    tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
    original_server_capacities = {server: (server.computation_capacity, server.bandwidth_capacity)
                                  for server in servers}

    # Batch greedy algorithm
    for batch_length in batch_lengths:
        batched_tasks = generate_batch_tasks(tasks, batch_length, time_steps)
        flattened_tasks = [task for tasks in batched_tasks for task in tasks]

        # Update the server capacities
        for server in servers:
            server.computation_capacity = original_server_capacities[server][0] * batch_length
            server.bandwidth_capacity = original_server_capacities[server][1] * batch_length

        greedy_result = online_batch_solver(batched_tasks, servers, batch_length, '', greedy_algorithm,
                                            value_density=UtilityDeadlinePerResource(ResourceSqrt()),
                                            server_selection_policy=SumResources(),
                                            resource_allocation_policy=SumPowPercentage())
        print(f'Batch length: {batch_length} - social welfare: {greedy_result.social_welfare}, '
              f'percentage run: {greedy_result.percentage_tasks_allocated}')
        tasks_allocated = [task.name for task in flattened_tasks if task.running_server is not None]
        print(f'Tasks allocated ({len(tasks_allocated)}): [{", ".join(tasks_allocated)}]')
        reset_model(flattened_tasks, servers)


def test_task_batching(model_dist=ModelDistribution('models/online_paper.mdl', num_servers=8),
                       time_steps: int = 10, mean_arrival_rate: int = 4, std_arrival_rate: float = 2):
    tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)

    batched_tasks = generate_batch_tasks(tasks, 3, time_steps)
    for pos, batch_task in enumerate(batched_tasks):
        print(f'Time step: {3 * pos} - [{", ".join([str(task.auction_time) for task in batch_task])}]')

    def flatten(tss):
        """
        Faltten all of the task from time based to 1 dimensional

        :param tss: Time series of batched tasks
        :return: List  of tasks
        """
        return [t for ts in tss for t in ts]

    batch1_tasks = flatten(generate_batch_tasks(tasks, 1, time_steps))
    batch2_tasks = flatten(generate_batch_tasks(tasks, 2, time_steps))
    batch3_tasks = flatten(generate_batch_tasks(tasks, 3, time_steps))

    for task_1, task_2, task_3 in zip(batch1_tasks, batch2_tasks, batch3_tasks):
        print(f'Task: {task_1.name}, deadlines: [{task_1.deadline}, {task_2.deadline}, {task_3.deadline}]')
