"""Analysis of the greedy results"""

from __future__ import annotations

import json
from typing import List, Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from seaborn.axisgrid import FacetGrid

matplotlib.rcParams['font.family'] = "monospace"


def print_optimal_percent_difference(files):
    """
    Prints the percentage difference of algorithm compared to the optimal
    :param files: The files
    """
    algo_difference = {}
    sub_optimals = {}
    total = {}
    for file in files:
        with open(file) as json_file:
            data = json.load(json_file)

            total[file] = len(data)
            for results in data:
                optimal = results['Optimal']
                max_algo = max(((value, algo) for algo, value in results.items()), key=lambda x: x[0])

                if max_algo[0] > optimal:
                    if file in sub_optimals:
                        sub_optimals[file] += 1
                    else:
                        sub_optimals[file] = 1
                    continue

                for result, value in results.items():
                    if result in algo_difference:
                        algo_difference[result].append(value / optimal)
                    else:
                        algo_difference[result] = [value / optimal]

    for file, sub_optimal in sub_optimals.items():
        print("{} has {} sub optimal solution of {}"
              .format(file.split("/")[-1].split(".")[0], sub_optimal, total[file]))
    print()

    for algo, percent_difference in sorted(algo_difference.items(), key=lambda x: np.mean(x[1]), reverse=True):
        print("Mean: {:6.3f}, Std: {:6.3f} - {}".format(np.mean(percent_difference), np.std(percent_difference), algo))


def plot_results(files: List[Tuple[str, str]], filename: str, aspect: float, attribute: str):
    """
    Plots the results from a file
    :param files: A file of results
    :param title: The graph title
    :param aspect: The aspect of the graph
    :param attribute:
    """
    data = []
    for file, model in files:
        with open(file) as json_file:
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
    for pos, (_, model) in enumerate(files):
        values = [np.mean(df[(df.model == model) & (df.algorithm == algo)][attribute]) for algo in df.algorithm.unique()]
        g.axes[0, pos].set_xlim(min(values) - 0.02, max(values) + 0.02)

    # g.fig.suptitle(title, size=16) Doesnt work
    # g.fig.subplots_adjust(top=1)

    plt.show()
    plt.savefig(filename + '.eps', format='eps')


def plot_relaxed(files: List[Tuple[str, str]]):
    """
    Plots the relaxed results
    :param files: A list of files
    """
    data = []

    for file, model in files:
        with open(file) as json_file:
            json_data = json.load(json_file)

            for results in json_data:
                if results['relaxed'][-1] is not None and results['optimal'][-1] is not None:
                    relaxed = results['relaxed'][-1]
                    optimal = results['optimal'][-1]

                    data.append((model, relaxed - optimal))

    df = pd.DataFrame(data, columns=['model', 'relaxed - optimal'])
    sns.scatterplot('model', 'relaxed - optimal', data=df)
    plt.show()


if __name__ == "__main__":
    optimal_files = [
        ("../results/august_23/greedy_results_j12_s2.txt", "12 Jobs 2 Servers"),
        ("../results/august_23/greedy_results_j15_s3.txt", "15 Jobs 3 Servers"),
        ("../results/august_23/greedy_results_j25_s5.txt", "25 Jobs 5 Servers")
    ]

    no_optimal_files = [
        ("../results/august_30/basic_j12_s2_no_optimal_greedy.txt", "12 Jobs 2 Servers"),
        ("../results/august_30/basic_j15_s3_no_optimal_greedy.txt", "15 Jobs 3 Servers"),
        ("../results/august_30/basic_j25_s5_no_optimal_greedy_1.txt", "25 Jobs 5 Servers")
    ]

    j25_s2_files = [
        ("../results/august_30/basic_j25_s5_no_optimal_greedy_1.txt", "1"),
        ("../results/august_30/basic_j25_s5_no_optimal_greedy_2.txt", "2"),
        ("../results/august_30/basic_j25_s5_no_optimal_greedy_3.txt", "3"),
        ("../results/august_30/basic_j25_s5_no_optimal_greedy_4.txt", "4"),
        ("../results/august_30/basic_j25_s5_no_optimal_greedy_5.txt", "5")
    ]

    relaxed_1_files = [
        ("../results/august_29/relaxed_results_j12_s2.txt", "12 Jobs 2 Servers"),
        ("../results/august_29/relaxed_results_j15_s3.txt", "15 Jobs 3 Servers"),
        ("../results/august_29/relaxed_results_j25_s5.txt", "25 Jobs 5 Servers")
    ]

    no_optimal_2_files = [
        ("../results/september_5/basic_j12_s2_no_optimal_greedy_test.txt", "12 Jobs 2 Servers"),
        ("../results/september_5/basic_j15_s3_no_optimal_greedy_test.txt", "15 Jobs 3 Servers"),
        ("../results/september_5/basic_j25_s5_no_optimal_greedy_test.txt", "25 Jobs 5 Servers"),
        ("../results/september_5/basic_j100_s20_no_optimal_greedy_test.txt", "100 Jobs 20 Servers"),
        ("../results/september_5/basic_j150_s25_no_optimal_greedy_test.txt", "150 Jobs 25 Servers"),
    ]

    optimal_2_files = [
        ("../results/september_6/basic_j12_s2_greedy_test.txt", "12 Jobs 2 Servers"),
        ("../results/september_6/basic_j15_s3_greedy_test.txt", "15 Jobs 3 Servers"),
        ("../results/september_6/basic_j25_s5_greedy_test.txt", "25 Jobs 5 Servers")
    ]

    relaxed_2_files = [
        ("../results/september_6/relaxed_results_j12_s2.txt", "12 Jobs 2 Servers"),
        ("../results/september_6/relaxed_results_j15_s3.txt", "15 Jobs 3 Servers"),
        ("../results/september_6/relaxed_results_j25_s5.txt", "25 Jobs 5 Servers")
    ]

    optimal_basic = [
        ("../results/september_20/optimal_greedy_test_basic_j12_s2_0.json", "12 Jobs 2 Servers"),
        ("../results/september_20/optimal_greedy_test_basic_j15_s2_0.json", "15 Jobs 2 Servers"),
        ("../results/september_20/optimal_greedy_test_basic_j15_s3_0.json", "15 Jobs 3 Servers"),
        ("../results/september_20/optimal_greedy_test_basic_j25_s5_0.json", "25 Jobs 5 Servers"),
        ("../results/september_20/optimal_greedy_test_basic_j50_s5_0.json", "50 Jobs 5 Servers")
    ]

    optimal_big_small = [
        ("../results/september_20/optimal_greedy_test_big_small_j12_s2_0.json", "12 Jobs 2 Servers"),
        ("../results/september_20/optimal_greedy_test_big_small_j15_s2_0.json", "15 Jobs 2 Servers"),
        ("../results/september_20/optimal_greedy_test_big_small_j15_s3_0.json", "15 Jobs 3 Servers"),
        ("../results/september_20/optimal_greedy_test_big_small_j25_s5_0.json", "25 Jobs 5 Servers"),
        ("../results/september_20/optimal_greedy_test_big_small_j50_s7_0.json", "50 Jobs 7 Servers"),
        ("../results/september_20/optimal_greedy_test_big_small_j75_s8_0.json", "75 Jobs 8 Servers"),
        ("../results/september_20/optimal_greedy_test_big_small_j100_s10_0.json", "100 Jobs 10 Servers")

    ]

    # plot_results(optimal_files, "Greedy results with Optimal", 1)
    # plot_results(no_optimal_files, "Greedy results without Optimal")
    # plot_results(j25_s2_files, "Greedy results without Optimal")
    # plot_relaxed(relaxed_1_files)
    # plot_results(no_optimal_2_files, "Greedy results without Optimal", 0.55)
    # plot_results(optimal_2_files, "Greedy results with Optimal", 0.75)
    # plot_relaxed(relaxed_2_files)

    plot_results(optimal_basic, "optimal_basic_value", 0.65, "sum value")
    plot_results(optimal_basic, "optimal_basic_percentage_jobs", 0.65, "percentage jobs")
    plot_results(optimal_big_small, "optimal_big_small_value", 0.65, "sum value")
    plot_results(optimal_big_small, "optimal_big_small_percentage_jobs", 0.65, "percentage jobs")
