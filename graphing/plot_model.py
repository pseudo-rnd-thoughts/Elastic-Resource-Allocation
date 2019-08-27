"""Graphing of models"""

from __future__ import annotations
from typing import List, Dict

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns

from core.job import Job
from core.result import Result, AlgorithmResults
from core.server import Server
from core.model import ModelDist

matplotlib.rcParams['font.family'] = "monospace"


# noinspection DuplicatedCode
def plot_jobs(jobs: List[Job], plot_utility_deadline: bool = True):
    """
    Plots the jobs on a graph
    :param jobs: A list of jobs to plot
    :param plot_utility_deadline: Plots the utility and deadline
    """
    if plot_utility_deadline:
        data = [[job.name, job.required_storage, job.required_computation, job.required_results_data,
                 job.utility, job.deadline] for job in jobs]
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


# noinspection DuplicatedCode
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


# noinspection DuplicatedCode
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


# noinspection DuplicatedCode
def plot_job_distribution(model_dists: List[ModelDist], repeats: int = 10):
    """
    Plots the job distribution of a list of models
    :param model_dists: A list of model distributions
    :param repeats: The number of repeats
    """
    data = [[model_dist.name.split(",")[0], job.required_storage, job.required_computation, job.required_results_data,
             job.utility, job.deadline]
            for model_dist in model_dists for _ in range(repeats) for job in model_dist.create()[0]]
    df = pd.DataFrame(data, columns=['Model', 'Storage', 'Computation', 'Results Data', 'Utility', 'Deadline'])
    wide_df = pd.melt(df, id_vars=['Model']).sort_values(['variable', 'value'])
    wide_df.rename(columns={'variable': 'Resource', 'value': 'Value'}, inplace=True)
    sns.catplot('Model', 'Value', hue='Resource', data=wide_df, kind='violin')
    plt.title("Job Distribution")
    plt.show()


# noinspection DuplicatedCode
def plot_server_distribution(model_dists: List[ModelDist], repeats: int = 10):
    """
    Plots the server distribution of a list of models
    :param model_dists: A list of model distributions
    :param repeats: The number of repeats
    """
    data = [[model_dist.name.split(",")[0], server.max_storage, server.max_computation, server.max_bandwidth]
            for model_dist in model_dists for _ in range(repeats) for server in model_dist.create()[1]]
    df = pd.DataFrame(data, columns=['Model', 'Storage', 'Computation', 'Results Data'])
    wide_df = pd.melt(df, id_vars=['Model']).sort_values(['variable', 'value'])
    wide_df.rename(columns={'variable': 'Resource', 'value': 'Value'}, inplace=True)
    sns.catplot('Model', 'Value', hue='Resource', data=wide_df, kind='violin')
    plt.title("Server Distribution")
    plt.show()

