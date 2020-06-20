"""
Tests the decentralised iterative auction
"""

from __future__ import annotations

import random as rnd
from copy import copy

from auctions.decentralised_iterative_auction import optimal_decentralised_iterative_auction, \
    greedy_decentralised_iterative_auction, PriceResourcePerDeadline, greedy_task_price, allocate_task
from core.core import reset_model, server_task_allocation, set_price_change
from greedy.resource_allocation_policy import SumPercentage
from extra.model import ModelDistribution


def test_optimal_dia():
    print()
    model = ModelDistribution('models/basic.mdl', 20, 3)
    tasks, servers = model.generate()
    set_price_change(servers, 5)

    result = optimal_decentralised_iterative_auction(tasks, servers, time_limit=1, debug_allocation=True)
    result.pretty_print()


def test_greedy_dia():
    print()
    model = ModelDistribution('models/basic.mdl', 20, 3)

    tasks, servers = model.generate()
    set_price_change(servers, 5)

    result = greedy_decentralised_iterative_auction(tasks, servers, PriceResourcePerDeadline(), SumPercentage(),
                                                    debug_allocation=True)
    result.pretty_print()


def test_greedy_task_price():
    print()
    model = ModelDistribution('models/basic.mdl', 20, 3)
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
    print(
        f'Server revenue: {server.revenue} - Task prices : {" ".join([str(task.price) for task in server.allocated_tasks])}')

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


def test_optimal_greedy_dia(repeats: int = 5):
    print()
    model = ModelDistribution('models/basic.mdl', 20, 3)

    print(f' Optimal    | Greedy')
    print(f'Time  | SW  | Time   | SW')
    for repeat in range(repeats):
        tasks, servers = model.generate()
        set_price_change(servers, 5)

        optimal_result = optimal_decentralised_iterative_auction(tasks, servers, time_limit=1)

        reset_model(tasks, servers)
        greedy_result = greedy_decentralised_iterative_auction(tasks, servers, PriceResourcePerDeadline(),
                                                               SumPercentage())

        print(f'{optimal_result.solve_time} | {optimal_result.social_welfare} | '
              f'{greedy_result.solve_time} | {greedy_result.social_welfare}')


if __name__ == "__main__":
    test_greedy_dia()
