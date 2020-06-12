"""Graph the allocation of resources from servers to tasks"""

from __future__ import annotations

from typing import List, Iterable, Dict

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docplex.cp.model import CpoModel, CpoVariable

from src.core.core import ImageFormat, save_plot
from src.core.server import Server
from src.core.task import Task

matplotlib.rcParams['font.family'] = 'monospace'


def minimise_resource_allocation(servers: List[Server]):
    for server in servers:
        model = CpoModel('MinimumAllocation')

        loading_speeds: Dict[Task, CpoVariable] = {}
        compute_speeds: Dict[Task, CpoVariable] = {}
        sending_speeds: Dict[Task, CpoVariable] = {}

        # The maximum bandwidth and the computation that the speed can be
        max_bandwidth, max_computation = server.bandwidth_capacity, server.computation_capacity

        # Loop over each task to allocate the variables and add the deadline constraints
        for task in server.allocated_tasks:
            loading_speeds[task] = model.integer_var(min=1, max=max_bandwidth,
                                                     name=f'{task.name} loading speed')
            compute_speeds[task] = model.integer_var(min=1, max=max_computation,
                                                     name=f'{task.name} compute speed')
            sending_speeds[task] = model.integer_var(min=1, max=max_bandwidth,
                                                     name=f'{task.name} sending speed')

            model.add((task.required_storage / loading_speeds[task]) +
                      (task.required_computation / compute_speeds[task]) +
                      (task.required_results_data / sending_speeds[task]) <= task.deadline)

        model.add(sum(task.required_storage for task in server.allocated_tasks) <= server.storage_capacity)
        model.add(sum(compute_speeds[task] for task in server.allocated_tasks) <= server.computation_capacity)
        model.add(sum(
            loading_speeds[task] + sending_speeds[task] for task in
            server.allocated_tasks) <= server.bandwidth_capacity)

        model.minimize(
            sum(loading_speeds[task] + compute_speeds[task] + sending_speeds[task] for task in server.allocated_tasks))

        model_solution = model.solve(log_output=None, TimeLimit=20)

        allocated_tasks = server.allocated_tasks.copy()
        server.reset_allocations()
        for task in allocated_tasks:
            task.reset_allocation()
            task.allocate(model_solution.get_value(loading_speeds[task]),
                          model_solution.get_value(compute_speeds[task]),
                          model_solution.get_value(sending_speeds[task]), server)


def plot_allocation_results(tasks: List[Task], servers: List[Server], title: str,
                            save_formats: Iterable[ImageFormat] = (), minimum_allocation: bool = False):
    """
    Plots the allocation results

    :param tasks: List of tasks
    :param servers: List of servers
    :param title: The title
    :param save_formats: The save format list
    :param minimum_allocation: If to use minimum allocation of tasks and servers
    """
    if minimum_allocation:
        minimise_resource_allocation(servers)

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

    axe.set_title(title, fontsize=18)

    pos = -0.1 if sum(task.running_server is not None for task in tasks) else 0.0
    server_resources_legend = [axe.bar(0, 0, color="gray", hatch=hatching * i) for i in range(3)]
    tasks_legend = axe.legend(h[:n_col], _l[:n_col], loc=[1.025, pos + 0.325], title=r'\textbf{Tasks}')
    plt.legend(server_resources_legend, ['Storage', 'Computation', 'Bandwidth'],
               loc=[1.025, pos], title=r'\textbf{Server resources}')
    axe.add_artist(tasks_legend)

    save_plot(title.lower().replace(' ', '_'), './figures/allocation', image_formats=save_formats)
    plt.show()
