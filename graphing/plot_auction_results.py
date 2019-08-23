"""Plots the auction results"""

from __future__ import annotations
from typing import List, Dict, Tuple
import operator

import json
import numpy as np


def mean_std_results(files):

    for file in files:
        print("File")
        with open(file) as json_file:
            difference_data = {}

            results: List[Dict[Tuple[str, int]]] = json.load(json_file)

            for result in results:
                max_value = max(result.values())
                for algorithm, value in result.items():
                    if algorithm not in difference_data:
                        difference_data[algorithm] = [max_value - value]
                    else:
                        difference_data[algorithm].append(max_value - value)

            data = [(np.mean(x), np.std(x), algorithm) for algorithm, x in difference_data.items()]
            for mean, std, algorithm in sorted(data, key=lambda x: x[0]):
                print("Mean {:.3f}, Std: {:.3f}, Algorithm: {}".format(mean, std, algorithm))

            print()


def optimal_results(files):
    for file in files:
        with open(file) as json_file:
            results = json.load(json_file)

            difference_data = {}
            percent = {}

            for result in results:
                if result['Optimal'] >= max([value for algo, value in result.items() if algo != "Optimal"]):
                    optimal_value = result['Optimal']
                    for algorithm, value in result.items():
                        if algorithm not in difference_data:
                            difference_data[algorithm] = [optimal_value - value]
                            percent[algorithm] = [value / optimal_value]
                        else:
                            difference_data[algorithm].append(optimal_value - value)
                            percent[algorithm].append(value / optimal_value)

            data = [(np.mean(x), np.std(x), np.mean(percent[algorithm]), algorithm) for algorithm, x in difference_data.items()]
            for mean, std, p, algorithm in sorted(data, key=lambda x: x[0]):
                print("Mean {:.3f}, Std: {:.3f}, Percent: {:.3}, Algorithm: {}".format(mean, std, p, algorithm))

            print()


if __name__ == "__main__":
    if False:
        mean_std_results(["../testing/iridis/new_results/greedy_results_Jobs 12 servers 2.txt",
                          "../testing/iridis/new_results/greedy_results_Jobs 15 servers 3.txt"])
    else:
        optimal_results(["../testing/iridis/new_results/greedy_results_Jobs 12 servers 2.txt",
                         "../testing/iridis/new_results/greedy_results_Jobs 15 servers 3.txt"])
