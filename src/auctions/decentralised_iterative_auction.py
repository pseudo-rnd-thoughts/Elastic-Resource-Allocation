"""Custom auctions by Mark and Seb"""

from __future__ import annotations

from math import inf
from random import choice
from time import time
from typing import List, Dict

from docplex.cp.model import CpoModel
from docplex.cp.solution import SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL

from src.core.core import allocate, print_model_solution
from src.core.result import Result
from src.core.server import Server
from src.core.task import Task


def assert_solution(loading_speeds: Dict[Task, int], compute_speeds: Dict[Task, int], sending_speeds: Dict[Task, int],
                    allocations: Dict[Task, bool]):
    """
    Assert that the solution is valid

    :param loading_speeds: The loading speeds
    :param compute_speeds: The compute speeds
    :param sending_speeds: The sending speeds
    :param allocations: The allocation of tasks
    """
    for task, allocation in allocations.items():
        if allocation:
            assert (task.required_storage * compute_speeds[task] * sending_speeds[task]) + \
                   (loading_speeds[task] * task.required_computation * sending_speeds[task]) + \
                   (loading_speeds[task] * compute_speeds[task] * task.required_results_data) <= \
                   (task.deadline * loading_speeds[task] * compute_speeds[task] * sending_speeds[task])


def evaluate_task_price(new_task: Task, server: Server, time_limit: int, initial_cost: int,
                        debug_results: bool = False, debug_initial_cost: bool = False):
    """
    Evaluates the task price to run on server using a vcg mechanism

    :param new_task: A new task
    :param server: A server
    :param time_limit: The solve time limit
    :param initial_cost: The initial cost of the task
    :param debug_results: Prints the result from the model solution
    :param debug_initial_cost: Prints the initial cost from the model solution
    :return: The results from the task prices
    """
    assert time_limit > 0, "Time limit: {}".format(time_limit)

    if debug_results:
        print(f'Evaluating task {new_task.name}\'s price on server {server.name}')
    model = CpoModel(f'Job {new_task.name} Price')

    # Add the new task to the list of server allocated tasks
    tasks = server.allocated_tasks + [new_task]

    # Create all of the resource speeds variables
    loading_speed = {task: model.integer_var(min=1, max=server.bandwidth_capacity - 1,
                                             name=f'Job {task.name} loading speed') for task in tasks}
    compute_speed = {task: model.integer_var(min=1, max=server.computation_capacity,
                                             name=f'Job {task.name} compute speed') for task in tasks}
    sending_speed = {task: model.integer_var(min=1, max=server.bandwidth_capacity - 1,
                                             name=f'Job {task.name} sending speed') for task in tasks}
    # Create all of the allocation variables however only on the currently allocated tasks
    allocation = {task: model.binary_var(name=f'Job {task.name} allocated') for task in server.allocated_tasks}

    # Add the deadline constraint
    for task in tasks:
        model.add((task.required_storage / loading_speed[task]) +
                  (task.required_computation / compute_speed[task]) +
                  (task.required_results_data / sending_speed[task]) <= task.deadline)

    # Add the server resource constraints
    model.add(sum(task.required_storage * allocated for task, allocated in allocation.items()) +
              new_task.required_storage <= server.storage_capacity)
    model.add(sum(compute_speed[task] * allocated for task, allocated in allocation.items()) +
              compute_speed[new_task] <= server.computation_capacity)
    model.add(sum((loading_speed[task] + sending_speed[task]) * allocated for task, allocated in allocation.items()) +
              (loading_speed[new_task] + sending_speed[new_task]) <= server.bandwidth_capacity)

    # The optimisation function
    model.maximize(sum(task.price * allocated for task, allocated in allocation.items()))

    # Solve the model with a time limit
    model_solution = model.solve(log_output=None, TimeLimit=time_limit)

    # If the model solution failed then return an infinite price
    if model_solution.get_solve_status() != SOLVE_STATUS_FEASIBLE and \
            model_solution.get_solve_status() != SOLVE_STATUS_OPTIMAL:
        print('Decentralised model failure')
        print_model_solution(model_solution)
        return inf, {}, {}, {}, {}, server, tasks

    # Get the max server profit that the model finds
    new_server_revenue = model_solution.get_objective_values()[0]

    # Calculate the task price through a vcg similar function
    task_price = server.revenue - new_server_revenue + server.price_change
    if task_price < initial_cost:  # Add an initial cost the task if the price is less than a set price
        if debug_initial_cost:
            print(f'Price set to {initial_cost} due to initial cost')
        task_price = initial_cost

    # Get the resource speeds and task allocations
    loading = {task: model_solution.get_value(loading_speed[task]) for task in tasks}
    compute = {task: model_solution.get_value(compute_speed[task]) for task in tasks}
    sending = {task: model_solution.get_value(sending_speed[task]) for task in tasks}
    allocation = {task: model_solution.get_value(allocated) for task, allocated in allocation.items()}

    # Check that the solution is valid
    assert_solution(loading, compute, sending, allocation)

    if debug_results:
        print(f'Sever: {server.name} - Prior revenue: {server.revenue}, new revenue: {new_server_revenue}, '
              f'price change: {server.price_change} therefore task price: {task_price}')

    return task_price, loading, compute, sending, allocation, server


def allocate_tasks(task_price: float, new_task: Task, server: Server,
                   loading: Dict[Task, int], compute: Dict[Task, int], sending: Dict[Task, int],
                   allocation: Dict[Task, bool], unallocated_tasks: List[Task],
                   debug_allocations: bool = False, debug_result: bool = False) -> int:
    """
    Allocates a task to a server based on the last allocation

    :param task_price: The new task price
    :param new_task: The new task
    :param server: The server the task is allocated to
    :param loading: A dictionary of loading speeds of tasks
    :param compute: A dictionary of compute speeds of tasks
    :param sending: A dictionary of sending speeds of tasks
    :param allocation: A dictionary of if a task is allocated to server
    :param unallocated_tasks: A list of all unallocated tasks
    :param debug_allocations: Debug the allocations
    :param debug_result: Debug results
    :return: The number of messages to allocate the task
    """
    server.reset_allocations()

    # Allocate the new task to the server
    new_task.reset_allocation()  # Possible bug where the task is not reset then allocated
    allocate(new_task, loading[new_task], compute[new_task], sending[new_task], server, task_price)
    messages = 1

    # For each of the task, if the task is allocated then allocate the task or reset the task
    for task, allocated in allocation.items():
        task.reset_allocation(forgot_price=False)
        if allocated:
            allocate(task, loading[task], compute[task], sending[task], server, task.price)
        else:
            unallocated_tasks.append(task)
            task.reset_allocation()
            messages += 1

        if debug_allocations:
            print(
                f"Job {task.name} is {'allocated' if allocation[task] else 'unallocated'} to server {server.name} "
                f"with loading {loading[task]}, compute {compute[task]} and sending {sending[task]}")
    if debug_result:
        print(f'{server.name}\'s total price: {server.revenue}')

    return messages


def decentralised_iterative_auction(tasks: List[Task], servers: List[Server], time_limit: int, initial_cost: int = 0,
                                    debug_allocation: bool = False, debug_results: bool = False) -> Result:
    """
    A decentralised iterative auctions created by Seb Stein and Mark Towers

    :param tasks: A list of tasks
    :param servers: A list of servers
    :param time_limit: The solve time limit
    :param initial_cost: An initial cost function
    :param debug_allocation: Debug the allocation process
    :param debug_results: Debugs the results
    :return: A list of prices at each iteration
    """
    start_time: float = time()

    # Checks that all of the server price change are greater than zero
    assert all(server.price_change > 0 for server in servers), \
        f"Price change - {', '.join(['{}: {}'.format(server.name, server.price_change) for server in servers])}"

    unallocated_tasks = tasks.copy()

    iterations: int = 0
    messages: int = 0

    # While there are unallocated task then loop
    while len(unallocated_tasks):
        # Choice a random task from the list
        task: Task = choice(unallocated_tasks)

        # Check that at least a single task can run the task else remove the task and continue the loop
        if any(server.can_empty_run(task) for server in servers) is False:
            unallocated_tasks.remove(task)
            continue

        # Calculate the min task price from all of the servers
        task_price, loading, compute, sending, allocation, server = \
            min((evaluate_task_price(task, server, time_limit, initial_cost)
                 for server in servers if server.can_empty_run(task)), key=lambda bid: bid[0])
        messages += 2 * len(servers)

        assert_solution(loading, compute, sending, allocation)

        # If the task price is less than the task value then allocate the task else remove the
        if task_price <= task.value:
            if debug_allocation:
                print(f'Adding task {task.name} to server {server.name} with price {task_price}')
            messages += allocate_tasks(task_price, task, server, loading, compute, sending, allocation,
                                       unallocated_tasks,
                                       debug_allocation, debug_results)
        elif debug_allocation:
            print(f'Removing Job {task.name} from the unallocated task as the '
                  f'min price is {task_price} and task value is {task.value}')
        unallocated_tasks.remove(task)

        if debug_allocation:
            print(f'Number of unallocated tasks: {len(unallocated_tasks)}\n')
        iterations += 1

    if debug_results:
        print(f'It is finished, number of iterations: {iterations} with '
              f'social welfare: {sum(server.revenue for server in servers)}')
        for server in servers:
            print(f'Server {server.name}: total revenue - {server.revenue}')
            print(f"\tJobs - {', '.join([f'{task.name}: £{task.price}' for task in server.allocated_tasks])}")

    return Result("DIA", tasks, servers, time() - start_time, individual_compute_time=time_limit, show_money=True,
                  total_iterations=iterations, total_messages=messages, initial_cost=initial_cost)
