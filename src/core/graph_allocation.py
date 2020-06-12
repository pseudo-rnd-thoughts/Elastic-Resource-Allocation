"""Graph the allocation of resources from servers to tasks"""

from __future__ import annotations

from typing import List, Iterable, Dict

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docplex.cp.model import CpoModel, CpoVariable

from core.core import ImageFormat, analysis_filename, save_plot
from core.job import Job
from core.server import Server

matplotlib.rcParams['font.family'] = "monospace"


def minimise_resource_allocation(servers: List[Server]):
    for server in servers:
        model = CpoModel("MinimumAllocation")

        loading_speeds: Dict[Job, CpoVariable] = {}
        compute_speeds: Dict[Job, CpoVariable] = {}
        sending_speeds: Dict[Job, CpoVariable] = {}

        # The maximum bandwidth and the computation that the speed can be
        max_bandwidth, max_computation = server.bandwidth_capacity, server.computation_capacity

        # Loop over each job to allocate the variables and add the deadline constraints
        for job in server.allocated_jobs:
            loading_speeds[job] = model.integer_var(min=1, max=max_bandwidth, name="{} loading speed".format(job.name))
            compute_speeds[job] = model.integer_var(min=1, max=max_computation,
                                                    name="{} compute speed".format(job.name))
            sending_speeds[job] = model.integer_var(min=1, max=max_bandwidth, name="{} sending speed".format(job.name))

            model.add((job.required_storage / loading_speeds[job]) +
                      (job.required_computation / compute_speeds[job]) +
                      (job.required_results_data / sending_speeds[job]) <= job.deadline)

        model.add(sum(job.required_storage for job in server.allocated_jobs) <= server.storage_capacity)
        model.add(sum(compute_speeds[job] for job in server.allocated_jobs) <= server.computation_capacity)
        model.add(sum(
            loading_speeds[job] + sending_speeds[job] for job in server.allocated_jobs) <= server.bandwidth_capacity)

        model.minimize(
            sum(loading_speeds[job] + compute_speeds[job] + sending_speeds[job] for job in server.allocated_jobs))

        model_solution = model.solve(log_output=None, TimeLimit=20)

        allocated_jobs = server.allocated_jobs.copy()
        server.reset_allocations()
        for job in allocated_jobs:
            job.reset_allocation()
            job.allocate(model_solution.get_value(loading_speeds[job]),
                         model_solution.get_value(compute_speeds[job]),
                         model_solution.get_value(sending_speeds[job]), server)


def plot_allocation_results(jobs: List[Job], servers: List[Server], title: str,
                            save_formats: Iterable[ImageFormat] = (), minimum_allocation: bool = False):
    """
    Plots the allocation results
    :param jobs: List of jobs
    :param servers: List of servers
    :param title: The title
    :param save_formats: The save format list
    """
    if minimum_allocation:
        minimise_resource_allocation(servers)

    allocated_jobs = [job for job in jobs if job.running_server]
    loading_df = pd.DataFrame(
        [[job.required_storage / server.storage_capacity if job.running_server == server else 0
          for job in allocated_jobs] for server in servers],
        index=[server.name for server in servers], columns=[job.name for job in allocated_jobs])
    compute_df = pd.DataFrame(
        [[job.compute_speed / server.computation_capacity if job.running_server == server else 0
          for job in allocated_jobs] for server in servers],
        index=[server.name for server in servers], columns=[job.name for job in allocated_jobs])
    sending_df = pd.DataFrame(
        [[(job.loading_speed + job.sending_speed) / server.bandwidth_capacity if job.running_server == server else 0
          for job in allocated_jobs] for server in servers],
        index=[server.name for server in servers], columns=[job.name for job in allocated_jobs])
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
