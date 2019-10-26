"""Analysis of the greedy results"""

from __future__ import annotations

import json
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from seaborn.axisgrid import FacetGrid

from core.core import decode_filename, save_plot, analysis_filename

matplotlib.rcParams['font.family'] = "monospace"


def plot_allocation_results(df_all: List[pd.DataFrame], title: str, labels: List[str], x_label: str, y_label: str):
    """
    PLots the server results
    :param df_all: A list of Dataframes to plot
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


def plot_results(encoded_filenames: List[str], x_axis: str, save: bool = False):
    """
    Plots the results from a file
    :param encoded_filenames: A list of encoded filenames
    :param x_axis: The x axis on the plot
    :param save: If to save the plot
    """
    data = []
    model_names: List[str] = []
    test_name: str = ""

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename(encoded_filename)
        model_names.append(model_name)

        with open(filename) as json_file:
            json_data = json.load(json_file)

            optimal_failures = 0
            for pos, algo_results in enumerate(json_data):
                if 'optimal' in algo_results and algo_results['optimal'] != "failure":
                    best = algo_results['optimal'][x_axis]
                    if best < max(result[x_axis] for algo, result in algo_results.items()
                                  if type(result) is dict and algo != "Relaxed"):
                        optimal_failures += 1
                else:
                    best = max(result[x_axis] for result in algo_results.values() if type(result) is dict)

                for algo, results in algo_results.items():
                    if type(results) is dict:
                        data.append((model_name, algo, pos, results[x_axis] / best))

            print("Optimal Failures: {}".format(optimal_failures))

    df = pd.DataFrame(data, columns=['model', 'algorithm', 'pos', x_axis])

    g = sns.FacetGrid(df, col='model', sharex=False)
    # noinspection PyUnresolvedReferences
    g: FacetGrid = (g.map(sns.barplot, x=x_axis, y='algorithm').set_titles("{col_name}"))

    for pos, model in enumerate(model_names):
        values = [np.mean(df[(df.model == model) & (df.algorithm == algo)][x_axis])
                  for algo in df.algorithm.unique()]
        g.axes[0, pos].set_xlim(min(values) - 0.02, max(values) + 0.02)

    if save:
        save_plot(analysis_filename(test_name, x_axis))
    plt.show()


if __name__ == "__main__":
    # Old results for greedy is august 23, 29, 30 and september 5, 6

    september_20_basic = [
        "september_20/optimal_greedy_test_basic_j12_s2_0",
        "september_20/optimal_greedy_test_basic_j15_s2_0",
        "september_20/optimal_greedy_test_basic_j15_s3_0",
        "september_20/optimal_greedy_test_basic_j25_s5_0",
        "september_20/optimal_greedy_test_basic_j50_s5_0"
    ]

    september_20_big_small = [
        "september_20/optimal_greedy_test_big_small_j12_s2_0",
        "september_20/optimal_greedy_test_big_small_j15_s2_0",
        "september_20/optimal_greedy_test_big_small_j15_s3_0",
        "september_20/optimal_greedy_test_big_small_j25_s5_0",
        "september_20/optimal_greedy_test_big_small_j50_s7_0",
        "september_20/optimal_greedy_test_big_small_j75_s8_0",
        "september_20/optimal_greedy_test_big_small_j100_s10_0"
    ]

    plot_results(september_20_basic, "sum value")
    plot_results(september_20_basic, "percentage jobs")
    plot_results(september_20_big_small, "sum value")
    plot_results(september_20_big_small, "percentage jobs")
