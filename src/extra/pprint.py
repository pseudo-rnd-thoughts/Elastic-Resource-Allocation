"""
Pretty print functions
"""

from typing import List, Tuple, Dict

from docplex.cp.solution import CpoSolveResult

from src.core.server import Server
from src.core.task import Task


def print_task_values(task_values: List[Tuple[Task, float]]):
    """
    Print the task utility values

    :param task_values: A list of tuples with the task and its value
    """
    print('\t\tJobs')
    max_task_name_len = max(len(task.name) for task, value in task_values) + 1
    print(f"{'Id':<{max_task_name_len}}| Value | Storage | Compute | models | Value | Deadline ")
    for task, value in task_values:
        # noinspection PyStringFormat
        print(
            f'{task.name:<{max_task_name_len}}|{value:^7.3f}|{task.required_storage:^9}|{task.required_computation:^9}|'
            f'{task.required_results_data:^8}|{task.value:^7.1f}|{task.deadline:^8}')
    print()


def print_task_allocation(tasks: List[Task]):
    """
    Prints the task allocation resource speeds

    :param tasks: List of tasks
    """
    print('Job Allocation')
    max_task_name_len = max(len(task.name) for task in tasks) + 1
    for task in tasks:
        if task.running_server:
            print(
                f"Job {task.name:<{max_task_name_len}} - Server {task.running_server.name}, loading: {task.loading_speed},"
                f" compute: {task.compute_speed}, sending: {task.sending_speed}")
        else:
            print(f'Job {task.name} - None')


def print_model_solution(model_solution: CpoSolveResult):
    """
    Print the model solution information

    :param model_solution: The model solution
    """
    print(f'Solve status: {model_solution.get_solve_status()}, Fail status: {model_solution.get_fail_status()}')
    print(f'Search status: {model_solution.get_search_status()}, Stop Cause: {model_solution.get_stop_cause()}, '
          f'Solve Time: {round(model_solution.get_solve_time(), 2)} secs')


def print_model(tasks: List[Task], servers: List[Server]):
    """
    Print the model

    :param tasks: The list of tasks
    :param servers: The list of servers
    """
    print('Job Name | Storage | Computation | Results Data | Value | Loading | Compute | Sending | Deadline | Price')
    for task in tasks:
        print(f'{task.name:^9s}|{task.required_storage:^9d}|{task.required_computation:^13d}|'
              f'{task.required_results_data:^14d}|{task.value:^7.1f}|{task.loading_speed:^9d}|{task.compute_speed:^9d}|'
              f'{task.sending_speed:^9d}|{task.deadline:^10d}| {task.price:.2f}')

    print('\nServer Name | Storage | Computation | Bandwidth | Allocated Jobs')
    for server in servers:
        print(f"{server.name:^12s}|{server.storage_capacity:^9d}|{server.computation_capacity:^13d}|"
              f"{server.bandwidth_capacity:^11d}| {', '.join([task.name for task in server.allocated_tasks])}")


def print_allocation(task_server_allocations: Dict[Server, List[Task]]):
    """
    Prints the task server allocation

    :param task_server_allocations: Dictionary of task server allocation
    """
    print(', '.join([f'{server.name} -> [{", ".join([task.name for task in tasks])}]'
                     for server, tasks in task_server_allocations.items()]))
