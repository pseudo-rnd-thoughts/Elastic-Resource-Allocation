"""Graphing of models"""

from __future__ import annotations

from typing import List

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

from core.job import Job
from core.model import ModelDist
from core.server import Server

matplotlib.rcParams['font.family'] = "monospace"


def plot_allocation_results(df_all: List[pd.DataFrame], title: str, labels: List[str], x_label: str, y_label: str):
    """
    PLots the server results
    :param df_all: A list of Dataframes to plot
    :param title: The titel
    :param labels: The labels
    :param x_label: The x label
    :param y_label: The y label
    """
    hatching = '/'

    n_df = len(df_all)
    n_col = len(df_all[0].columns)
    n_ind = len(df_all[0].index)
    axe = plt.subplot(111)

    for df in df_all:  # for each data frame
        axe = df.plot(kind="bar", linewidth=0, stacked=True, ax=axe, legend=False, grid=False)  # make bar plots

    h, _l = axe.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, n_df * n_col, n_col):  # len(h) = n_col * n_df
        for j, pa in enumerate(h[i:i + n_col]):
            for rect in pa.patches:  # for each index
                rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
                rect.set_hatch(hatching * int(i / n_col))  # edited part
                rect.set_width(1 / float(n_df + 1))

    axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(n_df + 1)) / 2.)
    axe.set_xticklabels(df_all[0].index, rotation=0)
    axe.set_title(title)
    axe.set_xlabel(x_label)
    axe.set_ylabel(y_label)

    # Add invisible data to add another legend
    n = []
    for i in range(n_df):
        n.append(axe.bar(0, 0, color="gray", hatch=hatching * i))

    l1 = axe.legend(h[:n_col], _l[:n_col], loc=[1.01, 0.5])
    if labels is not None:
        plt.legend(n, labels, loc=[1.01, 0.1])
    axe.add_artist(l1)
    plt.show()


def plot_jobs(jobs: List[Job], plot_utility_deadline: bool = True):
    """
    Plots the jobs on a graph
    :param jobs: A list of jobs to plot
    :param plot_utility_deadline: Plots the utility and deadline
    """
    if plot_utility_deadline:
        data = [[job.name, job.required_storage, job.required_computation, job.required_results_data,
                 job.value, job.deadline] for job in jobs]
        df = pd.DataFrame(data, columns=['Name', 'Storage', 'Computation', 'Results Data', 'Utility', 'Deadline'])
    else:
        data = [[job.name, job.required_storage, job.required_computation, job.required_results_data] for job in jobs]
        df = pd.DataFrame(data, columns=['Name', 'Storage', 'Computation', 'Results Data'])

    wide_df = pd.melt(df, id_vars=['Name']).sort_values(['variable', 'value'])
    wide_df.rename(columns={'variable': 'Resource'}, inplace=True)
    sns.barplot(x='value', y='Name', hue='Resource', data=wide_df)
    plt.ylabel('Name')
    plt.title("Jobs")
    plt.show()


def plot_servers(servers: List[Server]):
    """
    Plots the severs on a graph
    :param servers: A list of servers to plot
    """
    data = [[server.name, server.max_storage, server.max_computation, server.max_bandwidth] for server in servers]
    df = pd.DataFrame(data, columns=['Name', 'Storage', 'Computation', 'Bandwidth'])
    wide_df = pd.melt(df, id_vars=['Name']).sort_values(['variable', 'value'])
    wide_df.rename(columns={'variable': 'Resource'}, inplace=True)
    sns.barplot(x='Name', y='value', hue='Resource', data=wide_df)
    plt.xlabel('Name')
    plt.title("Servers")
    plt.show()


def plot_server_jobs_allocations(servers: List[Server]):
    """
    Plots the server jobs allocations
    :param servers: A list of servers to plot
    """
    server_names = [server.name for server in servers]
    allocated_jobs = [job for server in servers for job in server.allocated_jobs]
    job_names = [job.name for job in allocated_jobs]
    storage_df = pd.DataFrame([[job.required_storage/server.max_storage if job in server.allocated_jobs else 0
                                for job in allocated_jobs] for server in servers],
                              index=server_names, columns=job_names)
    compute_df = pd.DataFrame([[job.compute_speed/server.max_computation if job in server.allocated_jobs else 0
                                for job in allocated_jobs] for server in servers],
                              index=server_names, columns=job_names)
    bandwidth_df = pd.DataFrame([[(job.loading_speed + job.sending_speed)/server.max_bandwidth
                                  if job in server.allocated_jobs else 0
                                  for job in allocated_jobs] for server in servers],
                                index=server_names, columns=job_names)

    df_all = [storage_df, compute_df, bandwidth_df]
    labels = ['storage', 'compute', 'bandwidth']
    title = 'Server Job allocations'

    plot_allocation_results(df_all, title, labels, "Servers", "Percentage of Server resources")


def plot_job_distribution(model_dists: List[ModelDist], repeats: int = 10000):
    """
    Plots the job distribution of a list of models
    :param model_dists: A list of model distributions
    :param repeats: The number of repeats
    """

    """
    data = [[model_dist.name.split(",")[0], job.required_storage, job.required_computation, job.required_results_data,
             job.value, job.deadline]
            for model_dist in model_dists for _ in range(repeats) for job in model_dist.create()[0]]

    df = pd.DataFrame(data, columns=['Model', 'Storage', 'Computation', 'Results Data', 'Utility', 'Deadline'])
    wide_df = pd.melt(df, id_vars=['Model']).sort_values(['variable', 'value'])
    wide_df.rename(columns={'variable': 'Resource', 'value': 'Value'}, inplace=True)

    sns.catplot('Resource', 'Value', hue='Model', data=wide_df, kind='violin')
    plt.title("Job Distribution")
    plt.show()
    """

    data = []
    for model_dist in model_dists:
        for _ in range(repeats):
            jobs = model_dist.create()[0]
            for job in jobs:
                data.append((model_dist.dist_name, "Storage", job.required_storage))
                data.append((model_dist.dist_name, "Computation", job.required_computation))
                data.append((model_dist.dist_name, "Bandwidth", job.required_results_data))
                data.append((model_dist.dist_name, "Value", job.value))
                data.append((model_dist.dist_name, "Deadline", job.deadline))

    df = pd.DataFrame(data, columns=['Model', 'Resource', 'Value'])

    g = sns.FacetGrid(df, col='Resource', sharey=False, col_wrap=3)
    # noinspection PyUnresolvedReferences
    (g.map(sns.violinplot, 'Model', 'Value').set_titles('{col_name}'))
    plt.show()


def plot_server_distribution(model_dists: List[ModelDist], repeats: int = 10):
    """
    Plots the server distribution of a list of models
    :param model_dists: A list of model distributions
    :param repeats: The number of repeats
    """

    data = [[model_dist.dist_name, server.max_storage, server.max_computation, server.max_bandwidth]
            for model_dist in model_dists for _ in range(repeats) for server in model_dist.create()[1]]

    df = pd.DataFrame(data, columns=['Model', 'Storage', 'Computation', 'Results Data'])
    df = pd.melt(df, id_vars=['Model']).sort_values(['variable', 'value'])
    df.rename(columns={'variable': 'Resource', 'value': 'Value'}, inplace=True)

    sns.violinplot('Resource', 'Value', hue='Model', data=df)
    plt.title("Server Distribution")
    plt.show()
