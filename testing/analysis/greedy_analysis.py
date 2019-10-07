"""Analysis of the greedy results"""

from __future__ import annotations

import json
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from core.core import decode_filename, save_plot, analysis_filename, save_eps

matplotlib.rcParams['font.family'] = "monospace"


def plot_allocation_results(df_all: List[pd.DataFrame], title: str, labels: List[str], x_label: str, y_label: str):
    """
    PLots the server results
    :param df_all: A list of data frames to plot
    :param title: The title
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


def all_algorithms_analysis(encoded_filenames: List[str], x_axis: str, title: str, save: bool = False):
    """
    All Algorithm test results analysis
    :param encoded_filenames: List of encoded filenames
    :param x_axis: The X axis to plot
    :param save: If to save the plot
    """
    data = []
    model_names: List[str] = []
    test_name: str = ""

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename("greedy", encoded_filename)
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

    g = sns.FacetGrid(df, col='Model Name', sharex=False, height=6, margin_titles=True)
    g: sns.FacetGrid = (g.map(sns.barplot, x=x_axis, y='Algorithm Name', data=df).set_titles('{col_name}'))

    """
    for pos, model in enumerate(model_names):
        values = [np.mean(df[(df['Model Name'] == model) & (df['Algorithm Name'] == algo)][x_axis])
                  for algo in df['Algorithm Name'].unique()]
        print(model, min(values), max(values))
        g.axes[0, pos].set_xlim(min(values) * 0.98, max(values) * 1.02)
    """

    g.fig.subplots_adjust(top=0.9)
    g.fig.suptitle(title)

    if save:
        save_plot(analysis_filename(test_name, x_axis))
    plt.show()


if __name__ == "__main__":
    # Old results for greedy is august 23, 29, 30 and september 5, 6
    save_eps = False

    basic = [
        "optimal_greedy_test_basic_j12_s2_0",
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

    for model_files, model_name in [(basic, "basic"), (big_small, "big small")]:
        for attribute in ['Sum Value', 'Percentage Jobs', 'Solve Time', 'Best Sum Value', 'Best Percentage Jobs']:
            all_algorithms_analysis(model_files, attribute, "{} of {} model".format(attribute, model_name), save=True)
