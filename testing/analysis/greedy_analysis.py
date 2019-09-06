"""Analysis of the greedy results"""

from __future__ import annotations
from typing import List, Tuple

import json
import numpy as np
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

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


def plot_results(files, title, aspect):
    """
    Plots the results from a file
    :param files: A file of results
    :param title: The graph title
    """
    data = []
    for file, model in files:
        algo_difference = {}
        with open(file) as json_file:
            json_data = json.load(json_file)

            for results in json_data:
                if 'Optimal' in results:
                    best = results['Optimal']
                    if best < max(value for value in results.values()):
                        continue
                else:
                    best = max(value for value in results.values())

                for result, value in results.items():
                    if value is not None and value < best:
                        if result in algo_difference:
                            algo_difference[result].append(value / best)
                        else:
                            algo_difference[result] = [value / best]

        for algo, percent_difference in sorted(algo_difference.items(), key=lambda x: np.mean(x[1])):
            data.append((model, algo, np.mean(percent_difference)))

    df = pd.DataFrame(data, columns=['model', 'algorithm', 'value'])

    g = sns.FacetGrid(df, col='model', height=6, aspect=aspect, sharex=False)
    # noinspection PyUnresolvedReferences
    g = (g.map(sns.barplot, 'value', 'algorithm').set_titles("{col_name}"))
    g.fig.suptitle(title, size=16)
    g.fig.subplots_adjust(top=1)
    plt.show()


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

    relaxed_files = [
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

    # plot_results(optimal_files, "Greedy results with Optimal", 1)
    # plot_results(no_optimal_files, "Greedy results without Optimal")
    # plot_results(j25_s2_files, "Greedy results without Optimal")
    plot_relaxed(relaxed_files)
    # plot_results(no_optimal_2_files, "Greedy results without Optimal", 0.55)
    # plot_results(optimal_2_files, "Greedy results with Optimal", 1)
