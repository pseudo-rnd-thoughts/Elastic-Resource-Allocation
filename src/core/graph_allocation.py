"""Graph the allocation of resources from servers to tasks"""

from __future__ import annotations

from typing import List, Iterable, Dict

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docplex.cp.model import CpoModel, CpoVariable

from core.core import ImageFormat, analysis_filename, save_plot
from core.server import Server
from core.task import Task

matplotlib.rcParams['font.family'] = "monospace"


def minimise_resource_allocation(servers: List[Server]):
    for server in servers:
        model = CpoModel("MinimumAllocation")

        loading_speeds: Dict[Task, CpoVariable] = {}
        compute_speeds: Dict[Task, CpoVariable] = {}
        sending_speeds: Dict[Task, CpoVariable] = {}

        # The maximum bandwidth and the computation that the speed can be
        max_bandwidth, max_computation = server.bandwidth_capacity, server.computation_capacity

        # Loop over each task to allocate the variables and add the deadline constraints
        for task in server.allocated_tasks:
            loading_speeds[task] = model.integer_var(min=1, max=max_bandwidth,
                                                     name="{} loading speed".format(task.name))
            compute_speeds[task] = model.integer_var(min=1, max=max_computation,
                                                     name="{} compute speed".format(task.name))
            sending_speeds[task] = model.integer_var(min=1, max=max_bandwidth,
                                                     name="{} sending speed".format(task.name))

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
    resource_df = [loading_df, compute_df, sending_df]

    hatching = '\\'

    n_row = len(resource_df)
    n_col = len(resource_df[0].columns)
    n_ind = len(resource_df[0].index)
    axe = plt.subplot(111)

    for df in resource_df:  # for each data frame
        axe = df.plot(kind="bar", linewidth=0, stacked=True, ax=axe, legend=False, grid=False)  # make bar plots

    h, _l = axe.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, n_row * n_col, n_col):  # len(h) = n_col * n_df
        for j, pa in enumerate(h[i:i + n_col]):
            for rect in pa.patches:  # for each index
                rect.set_x(rect.get_x() + 1 / float(n_row + 1) * i / float(n_col))
                rect.set_hatch(hatching * int(i / n_col))
                rect.set_width(1 / float(n_row + 1))

    axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(n_row + 1)) / 2.)
    axe.set_xticklabels(resource_df[0].index, rotation=0)
    axe.set_title(title)
    axe.set_xlabel("Servers")
    axe.set_ylabel("Resource usage (%)")

    # Add invisible data to add another legend
    n = []
    for i in range(3):
        n.append(axe.bar(0, 0, color="gray", hatch=hatching * i))

    l1 = axe.legend(h[:n_col], _l[:n_col], loc=[1.01, 0.25])
    lgd = plt.legend(n, ['Storage', 'Computation', 'Bandwidth'], loc=[1.01, 0.05])
    axe.add_artist(l1)

    save_plot(analysis_filename("", title.lower().replace(" ", "_")), "allocation",
              image_formats=save_formats, lgd=lgd)
    plt.show()
