"""Graph the allocation of resources from servers to tasks"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docplex.cp.model import CpoModel, CpoVariable, SOLVE_STATUS_FEASIBLE, SOLVE_STATUS_OPTIMAL

from src.core.core import server_task_allocation
from src.extra.io import ImageFormat, save_plot

if TYPE_CHECKING:
    from typing import List, Iterable, Dict

    from src.core.server import Server
    from src.core.task import Task

matplotlib.rcParams['font.family'] = 'monospace'
matplotlib.rc('text', usetex=True)


def minimise_resource_allocation(tasks: List[Task], servers: List[Server], time_limit: int = 1):
    """
    Minimise resource allocation of a list of servers

    :param tasks: List of new tasks to the server (this is important for the online flexible case)
    :param servers: List of servers
    :param time_limit: Solve time limit
    """
    for server in servers:
        server_new_tasks = [task for task in server.allocated_tasks if task in tasks]
        model = CpoModel('MinimumAllocation')

        loading_speeds: Dict[Task, CpoVariable] = {}
        compute_speeds: Dict[Task, CpoVariable] = {}
        sending_speeds: Dict[Task, CpoVariable] = {}

        # The maximum bandwidth and the computation that the speed can be
        max_bandwidth = sum(task.loading_speed + task.sending_speed for task in server_new_tasks)
        max_computation = sum(task.compute_speed for task in server_new_tasks)
        assert 1 <= max_bandwidth and 1 <= max_computation, f'Max bandwidth: {max_bandwidth}, computation: {max_computation}'

        # Loop over each task to allocate the variables and add the deadline constraints
        for task in server_new_tasks:
            loading_speeds[task] = model.integer_var(min=1, max=max_bandwidth)
            compute_speeds[task] = model.integer_var(min=1, max=max_computation)
            sending_speeds[task] = model.integer_var(min=1, max=max_bandwidth)

            model.add((task.required_storage / loading_speeds[task]) +
                      (task.required_computation / compute_speeds[task]) +
                      (task.required_results_data / sending_speeds[task]) <= task.deadline)

        model.add(sum(compute_speeds[task] for task in server_new_tasks) <= max_computation)
        model.add(sum(loading_speeds[task] + sending_speeds[task] for task in server_new_tasks) <= max_bandwidth)

        model.minimize(
            (sum(loading_speeds[task] + sending_speeds[task] for task in server_new_tasks) / max_bandwidth) ** 3 +
            (sum(compute_speeds[task] for task in server_new_tasks) / max_computation) ** 3)

        model_solution = model.solve(log_output=None, TimeLimit=time_limit)

        # Check that it is solved
        if model_solution.get_solve_status() != SOLVE_STATUS_FEASIBLE and \
                model_solution.get_solve_status() != SOLVE_STATUS_OPTIMAL:
            print(f'Minimise {server.name} server resources allocated failed: {model_solution.get_solve_status()}')
            continue

        allocated_tasks = server.allocated_tasks.copy()
        server.reset_allocations()
        for task in allocated_tasks:
            if task in server_new_tasks:
                task.reset_allocation()
                server_task_allocation(server, task,
                                       model_solution.get_value(loading_speeds[task]),
                                       model_solution.get_value(compute_speeds[task]),
                                       model_solution.get_value(sending_speeds[task]))
            else:
                server.allocate_task(task)


def plot_allocation_results(tasks: List[Task], servers: List[Server], title: str,
                            save_formats: Iterable[ImageFormat] = (ImageFormat.PNG, ImageFormat.EPS, ImageFormat.PDF)):
    """
    Plots the allocation results

    :param tasks: List of tasks
    :param servers: List of servers
    :param title: The title
    :param save_formats: The save format list
    """

    allocated_tasks = [task for task in tasks if task.running_server]
    loading_df = pd.DataFrame(
        [[task.required_storage / server.storage_capacity if task.running_server == server else 0
          for task in allocated_tasks] for server in servers],
        index=[server.name for server in servers], columns=[task.name for task in allocated_tasks])
    compute_df = pd.DataFrame(
        [[task.compute_speed / server.computation_capacity if task.running_server == server else 0
          for task in allocated_tasks] for server in servers],
        index=[server.name for server in servers], columns=[task.name for task in allocated_tasks])
    sending_df = pd.DataFrame(
        [[(task.loading_speed + task.sending_speed) / server.bandwidth_capacity if task.running_server == server else 0
          for task in allocated_tasks] for server in servers],
        index=[server.name for server in servers], columns=[task.name for task in allocated_tasks])
    resources_df = [loading_df, compute_df, sending_df]

    n_col, n_ind = len(resources_df[0].columns), len(resources_df[0].index)
    hatching = '\\'

    axe = plt.subplot(111)
    for resource_df in resources_df:  # for each data frame
        axe = resource_df.plot(kind='bar', linewidth=0, stacked=True, ax=axe, legend=False, grid=False)

    h, _l = axe.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, 3 * n_col, n_col):
        for j, pa in enumerate(h[i:i + n_col]):
            for rect in pa.patches:
                rect.set_x(rect.get_x() + 1 / float(3 + 1) * i / float(n_col) - 0.125)
                rect.set_hatch(hatching * int(i / n_col))
                rect.set_width(1 / float(3 + 1))

    axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(3 + 1)) / 2. - 0.125)
    axe.set_xticklabels(resources_df[0].index, rotation=0)
    axe.set_xlabel(r'\textbf{Servers}', fontsize=12)

    axe.set_ylabel(r'\textbf{Resource Usage}', fontsize=12)
    axe.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    axe.set_yticklabels([r'0\%', r'20\%', r'40\%', r'60\%', r'80\%', r'100\%'])

    axe.set_title(title, fontsize=16)

    pos = -0.1 if sum(task.running_server is not None for task in tasks) else 0.0
    server_resources_legend = [axe.bar(0, 0, color="gray", hatch=hatching * i) for i in range(3)]
    tasks_legend = axe.legend(h[:n_col], _l[:n_col], loc=[1.025, pos + 0.325], title=r'\textbf{Tasks}')
    plt.legend(server_resources_legend, ['Storage', 'Computation', 'Bandwidth'],
               loc=[1.025, pos], title=r'\textbf{Server resources}')
    axe.add_artist(tasks_legend)

    save_plot(title.lower().replace(' ', '_'), 'example_allocation', image_formats=save_formats)
    plt.show()
