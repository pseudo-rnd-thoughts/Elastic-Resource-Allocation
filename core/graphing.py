"""Graphing of models"""

from __future__ import annotations
from typing import List, Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from core.job import Job
from core.result import Result, AlgorithmResults
from core.server import Server


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

    dfall = [storage_df, compute_df, bandwidth_df]
    labels = ['storage', 'compute', 'bandwidth']
    title = 'Server Job allocations'

    plot_server_results(dfall, title, labels)


def plot_algorithms_results(results: List[Result]):
    """
    Plots the algorithm results with a plot for the total utility, percentage utility and percentage jobs
    :param results: A list of results
    """
    data = [[result.algorithm_name, result.total_utility,
             result.percentage_total_utility, result.percentage_jobs_allocated]
            for result in results]

    df = pd.DataFrame(data, columns=['Algorithm Name', 'Total utility', 'Percentage utility', 'Percentage jobs'])
    df = pd.melt(df, id_vars=['Algorithm Name']).sort_values(['variable', 'value'])
    df.rename(columns={'variable': 'measure'}, inplace=True)

    g = sns.FacetGrid(df, col='measure', height=8, aspect=0.66, sharex=False)
    g.map(sns.barplot, 'value', 'Algorithm Name')

    plt.show()


def plot_repeat_algorithm_results(results: List[AlgorithmResults]):
    """
    Plots the repeat algorithm results for the total utility, percentage utility and percentage jobs
        of the mean and standard deviation
    :param results: A list of algorithm results
    """
    data = [[result.algorithm_name, 'total utility', utility]
            for result in results for utility in result.utility] + \
           [[result.algorithm_name, 'percentage utility', percentage_utility]
            for result in results for percentage_utility in result.percentage_utility] + \
           [[result.algorithm_name, 'percentage jobs', percentage_jobs]
            for result in results for percentage_jobs in result.percentage_jobs]

    df = pd.DataFrame(data, columns=['algorithm name', 'measure', 'value'])
    print(df)

    g = sns.FacetGrid(df, row='measure', height=2.5, aspect=4, sharey=False)
    g.map(sns.barplot, 'algorithm name', 'value', orient='h', ci=95)
    plt.show()


def plot_multi_models_results(model_results: Dict[str, List[AlgorithmResults]]):
    """
    Plot a multi model results
    :param model_results: The model results for all of the algorithms
    """
    data = [[model_name, result.algorithm_name, 'total utility', utility]
            for model_name, model_result in model_results.items()
            for result in model_result for utility in result.utility] + \
           [[model_name, result.algorithm_name, 'percentage utility', percentage_utility]
            for model_name, model_result in model_results.items()
            for result in model_result for percentage_utility in result.percentage_utility] + \
           [[model_name, result.algorithm_name, 'percentage jobs', percentage_jobs]
            for model_name, model_result in model_results.items()
            for result in model_result for percentage_jobs in result.percentage_jobs]

    df = pd.DataFrame(data, columns=['model name', 'algorithm name', 'measure', 'mean', 'std'])
    g = sns.FacetGrid(df, col='measure', height=4, aspect=4, sharey=False)
    g.map(sns.barplot, 'mean', 'model name', hue='algorithm name', orient='h')

    plt.xlabel('Test Name')
    plt.show()


# noinspection DuplicatedCode
def plot_auction_result(servers: List[Server], name: str):
    """
    Plots the server jobs allocations
    :param servers: A list of servers to plot
    """
    server_names = [server.name for server in servers]
    allocated_jobs = [job for server in servers for job in server.allocated_jobs]
    job_names = [job.name for job in allocated_jobs]
    storage_df = pd.DataFrame([[job.required_storage / server.max_storage if job in server.allocated_jobs else 0
                                for job in allocated_jobs] for server in servers],
                              index=server_names, columns=job_names)
    compute_df = pd.DataFrame([[job.compute_speed / server.max_computation if job in server.allocated_jobs else 0
                                for job in allocated_jobs] for server in servers],
                              index=server_names, columns=job_names)
    bandwidth_df = pd.DataFrame([[(job.loading_speed + job.sending_speed) / server.max_bandwidth
                                  if job in server.allocated_jobs else 0
                                  for job in allocated_jobs] for server in servers],
                                index=server_names, columns=job_names)
    price_df = pd.DataFrame([[job.price/server.total_price if job in server.allocated_jobs else 0
                              for job in allocated_jobs] for server in servers],
                            index=server_names, columns=job_names)
    print(price_df)

    dfall = [storage_df, compute_df, bandwidth_df, price_df]
    labels = ['storage', 'compute', 'bandwidth', 'price']
    title = '{} Auction Allocation'.format(name)

    plot_server_results(dfall, title, labels)


def plot_server_results(dfall: List[pd.DataFrame], title: str, labels: List[str]):
    """
    PLots the server results
    :param dfall: A list of Dataframes to plot
    :param title: The titel
    :param labels: The labels
    """
    hatching = '/'

    n_df = len(dfall)
    n_col = len(dfall[0].columns)
    n_ind = len(dfall[0].index)
    axe = plt.subplot(111)

    for df in dfall:  # for each data frame
        axe = df.plot(kind="bar", linewidth=0, stacked=True, ax=axe, legend=False, grid=False)  # make bar plots

    h, _l = axe.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, n_df * n_col, n_col):  # len(h) = n_col * n_df
        for j, pa in enumerate(h[i:i + n_col]):
            for rect in pa.patches:  # for each index
                rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
                rect.set_hatch(hatching * int(i / n_col))  # edited part
                rect.set_width(1 / float(n_df + 1))

    axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(n_df + 1)) / 2.)
    axe.set_xticklabels(dfall[0].index, rotation=0)
    axe.set_title(title)
    axe.set_xlabel("Servers")

    # Add invisible data to add another legend
    n = []
    for i in range(n_df):
        n.append(axe.bar(0, 0, color="gray", hatch=hatching * i))

    l1 = axe.legend(h[:n_col], _l[:n_col], loc=[1.01, 0.5])
    if labels is not None:
        plt.legend(n, labels, loc=[1.01, 0.1])
    axe.add_artist(l1)
    plt.show()
