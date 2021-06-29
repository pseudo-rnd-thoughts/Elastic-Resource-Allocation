"""
Tests the evaluation online environment works as intended
"""

from __future__ import annotations

from math import ceil
from typing import Iterable, List

from src.core.core import reset_model
from src.core.non_elastic_task import NonElasticTask, SumSpeedPowResourcePriority
from src.core.server import Server
from src.core.elastic_task import ElasticTask
from src.extra.model import SyntheticModelDist
from src.extra.online import generate_batch_tasks, online_batch_solver
from src.extra.visualise import minimal_allocated_resources_solver
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation import SumPowPercentage
from src.greedy.server_selection import SumResources
from src.greedy.task_priority import UtilityDeadlinePerResourcePriority, SqrtResourcesPriority
from src.optimal.non_elastic_optimal import non_elastic_optimal_solver
from src.optimal.elastic_optimal import elastic_optimal_solver


def test_online_model_generation(model_dist=SyntheticModelDist(num_servers=8),
                                 time_steps: int = 250, batch_lengths: Iterable[int] = (1, 2, 4, 5),
                                 mean_arrival_rate: int = 4, std_arrival_rate: float = 2):
    print()
    tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
    print(f'Number of tasks per time step: '
          f'{[len([task for task in tasks if task.auction_time == time_step]) for time_step in range(time_steps)]}')

    for batch_length in batch_lengths:
        valid_tasks = [task for task in tasks if batch_length < task.deadline]
        batched_tasks = generate_batch_tasks(valid_tasks, batch_length, time_steps)
        print(f'Number of time steps: {time_steps}, batch length: {batch_length}, '
              f'number of batches: {len(batched_tasks)}')

        assert len(batched_tasks) == ceil(time_steps / batch_length)
        assert sum(len(batch_tasks) for batch_tasks in batched_tasks) == len(valid_tasks)
        assert all(0 < task.value for _tasks in batched_tasks for task in _tasks)
        assert all(0 < task.deadline for _tasks in batched_tasks for task in _tasks), \
            [str(task) for _tasks in batched_tasks for task in _tasks if task.deadline < 0]
        assert all(batch_num * batch_length <= task.auction_time < (batch_num + 1) * batch_length
                   for batch_num, _tasks in enumerate(batched_tasks) for task in _tasks)


def test_online_server_capacities(model_dist=SyntheticModelDist(num_servers=8),
                                  time_steps: int = 50, batch_length: int = 3,
                                  mean_arrival_rate: int = 4, std_arrival_rate: float = 2, capacities: float = 0.3):
    print()
    tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
    for server in servers:
        server.storage_capacity = int(server.storage_capacity * capacities)
        server.computation_capacity = int(server.computation_capacity * capacities)
        server.bandwidth_capacity = int(server.bandwidth_capacity * capacities)
    batched_tasks = generate_batch_tasks(tasks, batch_length, time_steps)
    print(f'Tasks per batch time step: [{", ".join([str(len(batch_tasks)) for batch_tasks in batched_tasks])}]')
    result = online_batch_solver(batched_tasks, servers, batch_length, 'Greedy', greedy_algorithm,
                                 task_priority=UtilityDeadlinePerResourcePriority(SqrtResourcesPriority()),
                                 server_selection_policy=SumResources(),
                                 resource_allocation_policy=SumPowPercentage())
    print(f'Social welfare percentage: {result.percentage_social_welfare}')
    print(result.data)


def test_optimal_solutions(model_dist=SyntheticModelDist(num_servers=8),
                           time_steps: int = 20, mean_arrival_rate: int = 4, std_arrival_rate: float = 2):
    tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)
    non_elastic_tasks = [NonElasticTask(task, SumSpeedPowResourcePriority()) for task in tasks]

    # batched_tasks = generate_batch_tasks(tasks, 1, time_steps)
    # optimal_result = online_batch_solver(batched_tasks, servers, 1, 'Online Elastic Optimal',
    #                                      minimal_allocated_resources_solver, solver_time_limit=2)
    # print(f'Optimal - Social welfare: {optimal_result.social_welfare}')
    # reset_model([], servers)

    non_elastic_batched_tasks = generate_batch_tasks(non_elastic_tasks, 1, time_steps)
    non_elastic_optimal_result = online_batch_solver(non_elastic_batched_tasks, servers, 1, 'Non-elastic Optimal',
                                                     non_elastic_optimal_solver, time_limit=2)
    print(f'\nNon-elastic Optimal - Social welfare: {non_elastic_optimal_result.social_welfare}')
    reset_model([], servers)

    batched_tasks = generate_batch_tasks(tasks, 4, time_steps)
    greedy_result = online_batch_solver(batched_tasks, servers, 4, 'Greedy', greedy_algorithm,
                                        task_priority=UtilityDeadlinePerResourcePriority(SqrtResourcesPriority()),
                                        server_selection_policy=SumResources(),
                                        resource_allocation_policy=SumPowPercentage())
    print(f'Greedy - Social welfare: {greedy_result.social_welfare}')


def test_batch_lengths(model_dist=SyntheticModelDist(num_servers=8),
                       batch_lengths: Iterable[int] = (1, 5, 10, 15), time_steps: int = 100,
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

        task_priority = UtilityDeadlinePerResourcePriority(SqrtResourcesPriority())
        server_selection_policy = SumResources()
        resource_allocation_policy = SumPowPercentage()
        name = f'Greedy {task_priority.name}, {server_selection_policy.name}, ' \
               f'{resource_allocation_policy.name}'
        greedy_result = online_batch_solver(batched_tasks, servers, batch_length, name,
                                            greedy_algorithm, task_priority=task_priority,
                                            server_selection_policy=server_selection_policy,
                                            resource_allocation_policy=resource_allocation_policy)
        results.append(greedy_result)
        print(f'Batch length: {batch_length}, social welfare percent: {greedy_result.percentage_social_welfare}, '
              f'social welfare: {greedy_result.social_welfare}')
        reset_model(flattened_tasks, servers)


def test_online_non_elastic_task():
    model_dist = SyntheticModelDist(num_servers=8)
    tasks, servers = model_dist.generate_online(20, 4, 2)
    non_elastic_tasks = [NonElasticTask(task, SumSpeedPowResourcePriority()) for task in tasks]
    batched_non_elastic_tasks = generate_batch_tasks(non_elastic_tasks, 5, 20)

    for batch_non_elastic_tasks in batched_non_elastic_tasks:
        for non_elastic_task in batch_non_elastic_tasks:
            time_taken = non_elastic_task.required_storage * non_elastic_task.compute_speed * non_elastic_task.sending_speed + \
                         non_elastic_task.loading_speed * non_elastic_task.required_computation * non_elastic_task.sending_speed + \
                         non_elastic_task.loading_speed * non_elastic_task.compute_speed * non_elastic_task.required_results_data
            assert time_taken <= non_elastic_task.deadline * non_elastic_task.loading_speed * \
                   non_elastic_task.compute_speed * non_elastic_task.sending_speed


def test_minimise_resources():
    model_dist = SyntheticModelDist(num_servers=8)
    tasks, servers = model_dist.generate_online(20, 4, 2)

    def custom_solver(_tasks: List[ElasticTask], _servers: List[Server],
                      solver_time_limit: int = 3, minimise_time_limit: int = 2):
        """
        A custom solver for the elastic optimal solver which then checks that resource allocation is valid then
            minimises resource allocation

        :param _tasks: List of tasks for the time interval
        :param _servers: List of servers
        :param solver_time_limit: elastic resource allocation time limit
        :param minimise_time_limit: Minimise resource allocation time limit
        """
        valid_servers = [server for server in servers if
                         1 <= server.available_computation and 1 <= server.available_bandwidth]
        server_availability = {server: (server.available_computation, server.available_bandwidth) for server in servers}
        elastic_optimal_solver(_tasks, valid_servers, solver_time_limit)

        for server, (compute_availability, bandwidth_availability) in server_availability.items():
            server_old_tasks = [task for task in server.allocated_tasks if task not in _tasks]
            max_bandwidth = server.bandwidth_capacity - sum(
                task.loading_speed + task.sending_speed for task in server_old_tasks)
            max_computation = server.computation_capacity - sum(task.compute_speed for task in server_old_tasks)
            assert compute_availability == max_computation, \
                f'Availability: {compute_availability}, actual: {max_computation}'
            assert bandwidth_availability == max_bandwidth, \
                f'Availability: {bandwidth_availability}, actual: {max_bandwidth}'

        minimal_allocated_resources_solver(_tasks, valid_servers, minimise_time_limit)

    batched_tasks = generate_batch_tasks(tasks, 1, 20)
    optimal_result = online_batch_solver(batched_tasks, servers, 1, 'Online Elastic Optimal',
                                         custom_solver, solver_time_limit=2)
    print(f'Optimal - Social welfare: {optimal_result.social_welfare}')
    reset_model([], servers)


def test_batch_length(model_dist=SyntheticModelDist(num_servers=8), batch_lengths=(1, 2, 3),
                      time_steps: int = 20, mean_arrival_rate: int = 4, std_arrival_rate: float = 2):
    print()
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
                                            task_priority=UtilityDeadlinePerResourcePriority(SqrtResourcesPriority()),
                                            server_selection_policy=SumResources(),
                                            resource_allocation_policy=SumPowPercentage())
        print(f'Batch length: {batch_length} - social welfare: {greedy_result.social_welfare}, '
              f'percentage run: {greedy_result.percentage_tasks_allocated}')
        tasks_allocated = [task.name for task in flattened_tasks if task.running_server is not None]
        print(f'Tasks allocated ({len(tasks_allocated)}): [{", ".join(tasks_allocated)}]')
        reset_model(flattened_tasks, servers)


def test_task_batching(model_dist=SyntheticModelDist(num_servers=8),
                       time_steps: int = 10, mean_arrival_rate: int = 4, std_arrival_rate: float = 2):
    tasks, servers = model_dist.generate_online(time_steps, mean_arrival_rate, std_arrival_rate)

    batched_tasks = generate_batch_tasks(tasks, 3, time_steps)
    for pos, batch_task in enumerate(batched_tasks):
        print(f'Time step: {3 * pos} - [{", ".join([str(task.auction_time) for task in batch_task])}]')

    def flatten(tss):
        """
        Flatten all of the task from time based (2 dimensional) to 1 dimensional

        :param tss: Time series of batched tasks
        :return: List  of tasks
        """
        return [t for ts in tss for t in ts]

    batch1_tasks = flatten(generate_batch_tasks(tasks, 1, time_steps))
    batch2_tasks = flatten(generate_batch_tasks(tasks, 2, time_steps))
    batch3_tasks = flatten(generate_batch_tasks(tasks, 3, time_steps))

    for task_1, task_2, task_3 in zip(batch1_tasks, batch2_tasks, batch3_tasks):
        print(f'Task: {task_1.name}, deadlines: [{task_1.deadline}, {task_2.deadline}, {task_3.deadline}]')
