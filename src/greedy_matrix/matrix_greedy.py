"""Greedy algorithm using a matrix of task and server resource allocation values"""

from __future__ import annotations

from time import time
from typing import List, Tuple

from docplex.cp.model import CpoModel

from src.core.core import allocate
from src.core.result import Result
from src.core.server import Server
from src.core.task import Task
from src.greedy_matrix.allocation_value_policy import AllocationValuePolicy


def allocate_resources(task: Task, server: Server, value: AllocationValuePolicy) -> Tuple[float, int, int, int]:
    """
    Calculates the value of a server task allocation with the resources allocated
    :param task: A task
    :param server: A server
    :param value: The value policy
    :return: The tuple of values and resource allocations
    """

    """
    Old code
    return max(((value.evaluate(task, server, s, w, r), s, w, r)
                for s in range(1, server.available_bandwidth + 1)
                for w in range(1, server.available_computation + 1)
                for r in range(1, server.available_bandwidth - s + 1)
                if task.required_storage * w * r + s * task.required_computation * r +
                s * w * task.required_results_data <= task.deadline * s * w * r), key=lambda x: x[0])
    """
    model = CpoModel("Matrix value")

    loading_speed = model.integer_var(min=1, max=server.available_bandwidth - 1, name="loading speed")
    compute_speed = model.integer_var(min=1, max=server.available_computation, name="compute speed")
    sending_speed = model.integer_var(min=1, max=server.available_bandwidth - 1, name="sending speed")

    model.add(task.required_storage / loading_speed + task.required_computation / compute_speed +
              task.required_results_data / sending_speed <= task.deadline)
    model.add(compute_speed <= server.available_computation)
    model.add(loading_speed + sending_speed <= server.available_bandwidth)

    model.maximize(value.evaluate(task, server, loading_speed, compute_speed, sending_speed))

    model_solution = model.solve(log_output=None)

    return model_solution.get_objective_values()[0], model_solution.get_value(loading_speed), \
        model_solution.get_value(compute_speed), model_solution.get_value(sending_speed)


def matrix_greedy(tasks: List[Task], servers: List[Server], allocation_value_policy: AllocationValuePolicy,
                  debug_allocation: bool = False, debug_pop: bool = False) -> Result:
    """
    A greedy algorithm that uses the idea of a matrix
    :param tasks: A list of tasks
    :param servers: A list of servers
    :param allocation_value_policy: The value matrix policy
    :param debug_allocation: Debugs the allocation
    :param debug_pop: Debugs the values that are popped
    :return: The results
    """
    start_time = time()

    # Generate the full allocation value matrix
    allocation_value_matrix = {(task, server): allocate_resources(task, server, allocation_value_policy)
                               for task in tasks for server in servers if server.can_run(task)}
    unallocated_tasks = tasks.copy()

    # Loop over the allocation matrix till there are no values left
    while len(allocation_value_matrix):
        (allocated_task, allocated_server), (v, s, w, r) = max(allocation_value_matrix.items(), key=lambda x: x[1][0])
        allocate(allocated_task, s, w, r, allocated_server)
        if debug_allocation:
            print("Job {} on Server {} with value {:.3f}, loading {} compute {} sending {}"
                  .format(allocated_task.name, allocated_server.name, v, s, w, r))

        # Remove the task from the allocation matrix
        for server in servers:
            if (allocated_task, server) in allocation_value_matrix:
                if debug_pop:
                    print("Pop task {} and server {}".format(allocated_task.name, server.name))
                allocation_value_matrix.pop((allocated_task, server))

        # Remove the task from the unallocated tasks and check if the allocated server can now not run any of the tasks
        unallocated_tasks.remove(allocated_task)
        for task in unallocated_tasks:
            # Update the allocation when the server is updated
            if allocated_server.can_run(task):
                allocation_value_matrix[(task, allocated_server)] = allocate_resources(task, allocated_server,
                                                                                       allocation_value_policy)
            # If task cant be run then remove the task
            elif (task, allocated_server) in allocation_value_matrix:
                if debug_pop:
                    print("Pop task {} and server {}".format(task.name, allocated_server.name))
                allocation_value_matrix.pop((task, allocated_server))
    return Result("Matrix Greedy " + allocation_value_policy.name, tasks, servers, solve_time=time() - start_time)
