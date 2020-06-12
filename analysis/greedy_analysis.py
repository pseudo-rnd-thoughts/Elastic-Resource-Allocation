"""Analysis of the greedy results"""

from __future__ import annotations

import json
from typing import List, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.core.core import decode_filename, save_plot, analysis_filename, ImageFormat
from src.core.visualise import plot_allocation_results
from src.core.model import load_dist, ModelDist, reset_model
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import SumPercentage
from src.greedy.server_selection_policy import SumResources
from src.greedy.value_density import ResourceSum
from src.optimal.optimal import optimal_algorithm


def allocation_analysis():
    """
    Allocation Analysis
    """
    dist_name, task_dist, server_dist = load_dist("../../models/basic_v2.json")
    model_dist = ModelDist(dist_name, task_dist, 20, server_dist, 2)
    tasks, servers = model_dist.create()

    # Optimal
    optimal_algorithm(tasks, servers, 15)
    plot_allocation_results(tasks, servers, "Optimal Allocation", ImageFormat.BOTH)
    reset_model(tasks, servers)

    # Greedy
    greedy_algorithm(tasks, servers, ResourceSum(), SumResources(), SumPercentage())

    plot_allocation_results(tasks, servers, "Greedy Allocation", ImageFormat.BOTH)


def all_algorithms_analysis(encoded_filenames: List[str], x_axis: str,
                            title: str, save_formats: Iterable[ImageFormat] = ()):
    """
    All Algorithm test results analysis
    :param encoded_filenames: List of encoded filenames
    :param x_axis: The X axis to plot
    :param title: The title at the top of the plot
    :param save_formats: List of save formats
    """
    data = []
    model_names: List[str] = []
    test_name: str = ''

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename('paper', encoded_filename)
        model_names.append(model_name)

        with open(filename) as file:
            json_data = json.load(file)

            for pos, results in enumerate(json_data):
                # Find the best results of sum value or percentage tasks from all of the algorithms
                best_sum_value = max(r['sum value'] for a, r in results.items()
                                     if a != 'Relaxed' and type(r) is dict)
                best_percentage_tasks = max(r['percentage tasks'] for a, r in results.items()
                                            if a != 'Relaxed' and type(r) is dict)
                for algo_name, algo_results in results.items():
                    if type(algo_results) is dict:  # Otherwise optimal or relaxed == 'failure'
                        data.append((pos, model_name, algo_name, algo_results['sum value'],
                                     algo_results['percentage tasks'], algo_results['solve_time'],
                                     algo_results['sum value'] / best_sum_value,
                                     algo_results['percentage tasks'] / best_percentage_tasks))

    df = pd.DataFrame(data, columns=['Pos', 'Model Name', 'Algorithm Name', 'Sum Value', 'Percentage Tasks',
                                     'Solve Time', 'Best Sum Value', 'Best Percentage Tasks'])
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

    save_plot(analysis_filename(test_name, x_axis), "greedy", image_formats=save_formats)
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
        for attribute in ['Sum Value', 'Percentage Tasks', 'Solve Time', 'Best Sum Value', 'Best Percentage Tasks']:
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
        for attribute in ['Sum Value', 'Percentage Tasks', 'Solve Time', 'Best Sum Value', 'Best Percentage Tasks']:
            all_algorithms_analysis(model_files, attribute, "{} of {} model".format(attribute, model_name),
                                    save_format=image_format)
    """

    # allocation_analysis()

    paper = [
        "flexible_greedy_fog_j15_s3_0",
        "flexible_greedy_fog_j20_s4_0",
        "flexible_greedy_fog_j30_s5_0"
    ]

    for attribute in ['Sum Value', 'Percentage Tasks', 'Solve Time', 'Best Sum Value', 'Best Percentage Tasks']:
        all_algorithms_analysis(paper, attribute, "{} of {} model".format(attribute, "fog"),
                                save_formats=[ImageFormat.EPS, ImageFormat.PNG])
