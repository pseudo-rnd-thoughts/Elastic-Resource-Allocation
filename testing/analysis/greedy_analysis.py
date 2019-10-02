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
