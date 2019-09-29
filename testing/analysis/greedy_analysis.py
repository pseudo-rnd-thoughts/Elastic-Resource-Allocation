"""Analysis of the greedy results"""

from __future__ import annotations

import json
from typing import List

from core.core import decode_filename

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from seaborn.axisgrid import FacetGrid

matplotlib.rcParams['font.family'] = "monospace"


def plot_results(encoded_files: List[str], aspect: float, attribute: str):
    """
    Plots the results from a file
    :param encoded_files: A file of results
    :param aspect: The aspect of the graph
    :param attribute: The attribute of the model on the x axis
    """
    data = []
    models = []

    for encoded_file in encoded_files:
        filename, model = decode_filename(encoded_file)
        models.append(model)

        with open(filename) as json_file:
            json_data = json.load(json_file)

            optimal_failures = 0
            for pos, algo_results in enumerate(json_data):
                if 'optimal' in algo_results and algo_results['optimal'] != "failure":
                    best = algo_results['optimal'][attribute]
                    if best < max(result[attribute] for algo, result in algo_results.items()
                                  if type(result) is dict and algo != "Relaxed"):
                        optimal_failures += 1
                else:
                    best = max(result[attribute] for result in algo_results.values() if type(result) is dict)

                for algo, results in algo_results.items():
                    if type(results) is dict:
                        data.append((model, algo, pos, results[attribute] / best))

            print("Optimal Failures: {}".format(optimal_failures))

    df = pd.DataFrame(data, columns=['model', 'algorithm', 'pos', attribute])

    g = sns.FacetGrid(df, col='model', height=6, aspect=aspect, sharex=False)
    # noinspection PyUnresolvedReferences
    g: FacetGrid = (g.map(sns.barplot, attribute, 'algorithm', ci=95).set_titles("{col_name}"))

    for pos, model in enumerate(models):
        values = [np.mean(df[(df.model == model) & (df.algorithm == algo)][attribute])
                  for algo in df.algorithm.unique()]
        g.axes[0, pos].set_xlim(min(values) - 0.02, max(values) + 0.02)

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

    plot_results(september_20_basic, 0.65, "sum value")
    plot_results(september_20_basic, 0.65, "percentage jobs")
    plot_results(september_20_big_small, 0.65, "sum value")
    plot_results(september_20_big_small, 0.65, "percentage jobs")
