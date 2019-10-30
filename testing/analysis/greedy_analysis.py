"""Analysis of the greedy results"""

from __future__ import annotations

import json
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from core.core import decode_filename, save_plot, analysis_filename, ImageFormat
from core.job import Job
from core.model import load_dist, ModelDist, reset_model
from core.server import Server
from greedy.greedy import greedy_algorithm
from greedy.resource_allocation_policy import SumPercentage
from greedy.server_selection_policy import SumResources
from greedy.value_density import ResourceSum
from optimal.optimal import optimal_algorithm

matplotlib.rcParams['font.family'] = "monospace"


def plot_allocation_results(jobs: List[Job], servers: List[Server], title: str,
                            save_format: ImageFormat = ImageFormat.NONE):
    """

    :param jobs:
    :param servers:
    :param title:
    :param save_format:
    """
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

    hatching = '/'

    n_col = len(resource_df[0].columns)
    n_ind = len(resource_df[0].index)
    axe = plt.subplot(111)

    for df in resource_df:  # for each data frame
        axe = df.plot(kind="bar", linewidth=0, stacked=True, ax=axe, legend=False, grid=False)  # make bar plots

    h, _l = axe.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, 3 * n_col, n_col):  # len(h) = n_col * n_df
        for j, pa in enumerate(h[i:i + n_col]):
            for rect in pa.patches:  # for each index
                rect.set_x(rect.get_x() + 1 / float(3 + 1) * i / float(n_col))
                rect.set_hatch(hatching * int(i / n_col))  # edited part
                rect.set_width(1 / float(3 + 1))

    axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(3 + 1)) / 2.)
    axe.set_xticklabels(resource_df[0].index, rotation=0)
    axe.set_title(title)
    axe.set_xlabel("Servers")
    axe.set_ylabel("Resource usage (%)")

    # Add invisible data to add another legend
    n = []
    for i in range(3):
        n.append(axe.bar(0, 0, color="gray", hatch=hatching * i))

    l1 = axe.legend(h[:n_col], _l[:n_col], loc=[1.01, 0.25])
    plt.legend(n, ['Storage', 'Computation', 'Bandwidth'], loc=[1.01, 0.05])
    axe.add_artist(l1)

    save_plot(analysis_filename("allocation", title.lower().replace(" ", "_")), "allocation", image_format=save_format)
    plt.show()


def allocation_analysis():
    """
    Allocation Analysis
    """
    dist_name, job_dist, server_dist = load_dist("../../models/basic_v2.json")
    model_dist = ModelDist(dist_name, job_dist, 20, server_dist, 2)
    jobs, servers = model_dist.create()

    # Optimal
    optimal_algorithm(jobs, servers, 15)
    plot_allocation_results(jobs, servers, "Optimal Allocation", ImageFormat.BOTH)
    reset_model(jobs, servers)

    # Greedy
    greedy_algorithm(jobs, servers, ResourceSum(), SumResources(), SumPercentage())

    plot_allocation_results(jobs, servers, "Greedy Allocation", ImageFormat.BOTH)


def all_algorithms_analysis(encoded_filenames: List[str], x_axis: str,
                            title: str, save_format: ImageFormat = ImageFormat.NONE):
    """
    All Algorithm test results analysis
    :param encoded_filenames: List of encoded filenames
    :param x_axis: The X axis to plot
    :param title: The title at the top of the plot
    :param save_format: If to save the plot
    """
    data = []
    model_names: List[str] = []
    test_name: str = ''

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename('greedy', encoded_filename)
        model_names.append(model_name)

        with open(filename) as file:
            json_data = json.load(file)

            for pos, results in enumerate(json_data):
                # Find the best results of sum value or percentage jobs from all of the algorithms
                best_sum_value = max(r['sum value'] for a, r in results.items()
                                     if a != 'Relaxed' and type(r) is dict)
                best_percentage_jobs = max(r['percentage jobs'] for a, r in results.items()
                                           if a != 'Relaxed' and type(r) is dict)
                for algo_name, algo_results in results.items():
                    if type(algo_results) is dict:  # Otherwise optimal or relaxed == 'failure'
                        data.append((pos, model_name, algo_name, algo_results['sum value'],
                                     algo_results['percentage jobs'], algo_results['solve_time'],
                                     algo_results['sum value'] / best_sum_value,
                                     algo_results['percentage jobs'] / best_percentage_jobs))

    df = pd.DataFrame(data, columns=['Pos', 'Model Name', 'Algorithm Name', 'Sum Value', 'Percentage Jobs',
                                     'Solve Time', 'Best Sum Value', 'Best Percentage Jobs'])
    df = df.loc[~((df['Algorithm Name'].str.contains('Greedy Utility * deadline / Sum', regex=False)) |
                  (df['Algorithm Name'].str.contains('Greedy Utility / Sqrt Sum', regex=False)) |
                  df['Algorithm Name'].str.contains('Matrix Greedy Sum Exp^3 Percentage', regex=False))]

    g = sns.FacetGrid(df, col='Model Name', sharex=False, height=5)
    g = g.map(sns.barplot, x_axis, 'Algorithm Name').set_titles("{col_name}")

    for pos, model in enumerate(model_names):
        values = [np.mean(df[(df['Model Name'] == model) & (df['Algorithm Name'] == algo)][x_axis])
                  for algo in df['Algorithm Name'].unique()]
        g.axes[0, pos].set_xlim(min(values) * 0.97, max(values) * 1.02)

    g.fig.subplots_adjust(top=0.88)
    g.fig.suptitle(title)

    save_plot(analysis_filename(test_name, x_axis), "greedy", image_format=save_format)
    plt.show()


if __name__ == "__main__":
    # Old results for greedy is august 23, 29, 30 and september 5, 6

    basic = [
        # "optimal_greedy_test_basic_j12_s2_0",
        # "optimal_greedy_test_basic_j15_s2_0",
        "optimal_greedy_test_basic_j15_s3_0",
        "optimal_greedy_test_basic_j25_s5_0",
        "optimal_greedy_test_basic_j50_s5_0"
    ]

    big_small = [
        "optimal_greedy_test_big_small_j12_s2_0",
        # "optimal_greedy_test_big_small_j15_s2_0",
        "optimal_greedy_test_big_small_j15_s3_0",
        "optimal_greedy_test_big_small_j25_s5_0",
        "optimal_greedy_test_big_small_j50_s7_0",
        "optimal_greedy_test_big_small_j75_s8_0",
        "optimal_greedy_test_big_small_j100_s10_0"
    ]

    # all_algorithms_analysis(basic, 'Sum Value', "{} of {} model".format('Sum Value', 'Basic'),
    #                         save_format=ImageFormat.BOTH)
    """
    image_format = ImageFormat.BOTH
    for model_files, model_name in [(basic, "Basic"), (big_small, "Big Small")]:
        for attribute in ['Sum Value', 'Percentage Jobs', 'Solve Time', 'Best Sum Value', 'Best Percentage Jobs']:
            all_algorithms_analysis(model_files, attribute, "{} of {} model".format(attribute, model_name),
                                    save_format=image_format)
    """

    big_small_a = [
        "optimal_greedy_test_big_small_j12_s2_0",
        # "optimal_greedy_test_big_small_j15_s2_0",
        "optimal_greedy_test_big_small_j15_s3_0",
        "optimal_greedy_test_big_small_j25_s5_0"
    ]

    big_small_b = [
        "optimal_greedy_test_big_small_j50_s7_0",
        "optimal_greedy_test_big_small_j75_s8_0",
        "optimal_greedy_test_big_small_j100_s10_0"
    ]

    """
    image_format = ImageFormat.BOTH
    for model_files, model_name in [(big_small_b, "Big Small")]:
        for attribute in ['Sum Value', 'Percentage Jobs', 'Solve Time', 'Best Sum Value', 'Best Percentage Jobs']:
            all_algorithms_analysis(model_files, attribute, "{} of {} model".format(attribute, model_name),
                                    save_format=image_format)
    """

    allocation_analysis()
