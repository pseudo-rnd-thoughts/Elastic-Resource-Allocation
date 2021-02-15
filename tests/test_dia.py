"""
Tests the decentralised iterative auction
"""

from __future__ import annotations

import json
import random as rnd
from copy import copy

from auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction, \
    greedy_decentralised_iterative_auction, PriceResourcePerDeadline, greedy_task_price, allocate_task
from core.core import reset_model, server_task_allocation, set_server_heuristics
from extra.io import results_filename, parse_args
from extra.model import ModelDistribution
from greedy.resource_allocation_policy import SumPercentage
from optimal.flexible_optimal import flexible_optimal


def test_greedy_task_price():
    print()
    model = ModelDistribution('../models/synthetic.mdl', 20, 3)
    tasks, servers = model.generate()

    server = servers[0]

    resource_allocation_policy = SumPercentage()
    for _ in range(10):
        task = tasks.pop(rnd.randint(0, len(tasks) - 1))
        if server.can_run(task):
            s, w, r = resource_allocation_policy.allocate(task, server)
            server_task_allocation(server, task, s, w, r, price=rnd.randint(1, 10))

    copy_tasks = [copy(task) for task in server.allocated_tasks]
    copy_server = copy(server)
    print(f'Server revenue: {server.revenue} - '
          f'Task prices : {" ".join([str(task.price) for task in server.allocated_tasks])}')

    new_task = tasks.pop(0)
    task_price, speeds = greedy_task_price(new_task, server, PriceResourcePerDeadline(), resource_allocation_policy,
                                           debug_revenue=True)
    print(f'Task Price: {task_price}')

    assert len(copy_tasks) == len(server.allocated_tasks)
    assert [
        task.loading_speed == copy_task.loading_speed and task.compute_speed == copy_task.compute_speed and
        task.sending_speed == copy_task.sending_speed and task.price == copy_task.price and
        task.name == copy_task.name and task.value == copy_task.value
        for copy_task, task in zip(copy_tasks, server.allocated_tasks)
    ]
    assert server.revenue == copy_server.revenue and server.available_storage == copy_server.available_storage and \
        server.available_computation == copy_server.available_computation and \
        server.available_bandwidth == copy_server.available_bandwidth

    unallocated_tasks = []
    allocate_task(new_task, task_price, server, unallocated_tasks, speeds)

    assert copy_server.revenue + 1 == server.revenue
    assert new_task.price == task_price
    assert all(task.loading_speed == 0 and task.compute_speed == 0 and task.sending_speed == 0 and task.price == 0
               for task in unallocated_tasks)
    for task in server.allocated_tasks:
        copy_task = next((copy_task for copy_task in copy_tasks if copy_task.name == task.name), None)
        if copy_task:
            assert task.loading_speed == copy_task.loading_speed and task.compute_speed == copy_task.compute_speed and \
                   task.sending_speed == copy_task.sending_speed and task.price == copy_task.price and \
                   task.value == copy_task.value and task.name == copy_task.name
        else:
            assert task.loading_speed == new_task.loading_speed and task.compute_speed == new_task.compute_speed and \
                   task.sending_speed == new_task.sending_speed and task.price == new_task.price and \
                   task.value == new_task.value and task.name == new_task.name


def test_optimal_vs_greedy_dia(repeats: int = 5):
    print()
    model = ModelDistribution('../models/synthetic.mdl', 20, 3)

    print(f' Optimal    | Greedy')
    print(f'Time  | SW  | Time   | SW')
    for repeat in range(repeats):
        tasks, servers = model.generate()
        set_server_heuristics(servers, price_change=5)

        optimal_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit=1)

        reset_model(tasks, servers)
        greedy_result = greedy_decentralised_iterative_auction(tasks, servers, PriceResourcePerDeadline(),
                                                               SumPercentage())

        print(f'{optimal_result.solve_time} | {optimal_result.social_welfare} | '
              f'{greedy_result.solve_time} | {greedy_result.social_welfare}')


def dia_social_welfare_test(model_dist: ModelDistribution, repeat: int, repeats: int = 20):
    """
    Evaluates the results using the optimality

    :param model_dist: The model distribution
    :param repeat: The repeat of the testing
    :param repeats: The number of repeats
    """
    data = []
    filename = results_filename('testing', model_dist, repeat)
    for _ in range(repeats):
        tasks, servers = model_dist.generate()
        model_results = {}

        optimal_result = flexible_optimal(tasks, servers, 30)
        model_results[optimal_result.algorithm] = optimal_result.store()
        reset_model(tasks, servers)

        for pos in range(5):
            set_server_heuristics(servers, price_change=3, initial_price=25)
            dia_result = optimal_decentralised_iterative_auction(tasks, servers, 2)
            model_results[f'DIA {pos}'] = dia_result
            reset_model(tasks, servers)

        data.append(model_results)

        # Save the results to the file
        with open(filename, 'w') as file:
            json.dump(data, file)


if __name__ == "__main__":
    args = parse_args()
    dia_social_welfare_test(ModelDistribution(args.file, args.tasks, args.servers), args.repeat)
