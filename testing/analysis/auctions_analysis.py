"""Auction Analysis"""

from __future__ import annotations
from typing import List

import json

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def print_auction_results(files: List[str]):
    """
    Prints the Auction results from a file
    :param files: The files to print
    """
    for file, model in files:
        print(model)
        with open(file) as json_file:
            data = json.load(json_file)

            print("Total utility for {}".format(file.split("/")[-1].split(".")[0]))
            for results in data:
                vcg = results['vcg'][0]
                iterative_results = {}
                for x in (1, 2, 3, 5, 7, 10):
                    name = 'iterative {}'.format(x)
                    if results[name][0] in iterative_results:
                        iterative_results[results[name][0]].append(str(x))
                    else:
                        iterative_results[results[name][0]] = [str(x)]

                print("VCG: {:4d}, {}".format(vcg, ', '.join('e{}: {}'.format(' '.join(names), value)
                                                             for value, names in iterative_results.items())))
            print()


def print_mutated_auction_results(files: List[str]):
    """
    Prints the mutated auction results
    :param files: The files to print
    """
    for file, model in files:
        print(model)
        with open(file) as json_file:
            data = json.load(json_file)

            for result in data:
                no_mutate = result['no mutation'][0]
                for name, values in result.items():
                    if name != "no mutation":
                        if no_mutate < values[0]:
                            print("{} total utility increase from {} to {}".format(name, no_mutate, values[0]))
                        if values[2] > values[3]:
                            print("{:.10} utility increase from {:.3f} to {}".format(name, values[2], values[3]))


def print_multiple_auction_results(files: List[str]):
    """
    Prints the multiple auction results
    :param files: The files to print
    """
    for file, model in files:
        print(model)
        with open(file) as json_file:
            data = json.load(json_file)

            for results in data:
                result = {}
                for price_change, (value, _) in results.items():
                    if value in result:
                        result[value].append(price_change)
                    else:
                        result[value] = [price_change]
                print("; ".join(["{}: {}".format(value, ', '.join(names)) for value, names in result.items()]))
        print()


def plot_auction_results(files, title):
    """
    Plots the auction results
    :param files: The files
    :param title: The title
    """
    data = []
    for file, model in files:
        with open(file) as json_file:
            json_data = json.load(json_file)

            for pos, results in enumerate(json_data):
                for name, result in results.items():
                    data.append((model, pos, name, result[0], result[1]))

    df = pd.DataFrame(data, columns=['model', 'pos', 'name', 'value', 'price'])
    g: sns.FacetGrid = sns.FacetGrid(df, col='model', col_wrap=2)
    # noinspection PyUnresolvedReferences
    g = (g.map(sns.scatterplot, 'pos', 'value', hue='name', data=df)
         .set_titles("{col_name}").add_legend())
    g.fig.subplots_adjust(top=0.9)
    g.fig.suptitle(title)
    plt.show()


if __name__ == "__main__":
    normal_files = [
        ("../results/august_23/auction_results_j12_s2.txt", "12 Jobs 2 Servers"),
        ("../results/august_23/auction_results_j15_s3.txt", "15 Jobs 3 Servers"),
        ("../results/august_23/auction_results_j25_s5.txt", "25 Jobs 5 Servers")
    ]

    single_price_auctions = [
        ("../results/august_26/single_price_auction_results_basic_j12_s2.txt", "12 Jobs 2 Servers"),
        ("../results/august_26/single_price_auction_results_basic_j25_s5.txt", "25 Jobs 5 Servers")
    ]

    multi_price_auction = [
        ("../results/august_30/multi_price_iterative_auction_results_basic_j12_s2.txt", "12 Jobs 2 Servers"),
        ("../results/august_30/multi_price_iterative_auction_results_basic_j15_s3.txt", "15 Jobs 3 Servers"),
        ("../results/august_30/multi_price_iterative_auction_results_basic_j25_s5.txt", "25 Jobs 5 Servers")
    ]

    mutated_price_auction = [
        ("../results/september_2/mutate_iterative_auction_basic_j12_s2.txt", "12 Jobs 2 Servers"),
        ("../results/september_2/mutate_iterative_auction_basic_j15_s3.txt", "15 Jobs 3 Servers"),
        ("../results/september_2/mutate_iterative_auction_basic_j25_s5.txt", "25 Jobs 5 Servers")
    ]

    mutated_price_2_auction = [
        ("../results/september_4/mutate_iterative_auction_basic_j12_s2.txt", "12 Jobs 2 Servers"),
        ("../results/september_4/mutate_iterative_auction_basic_j15_s3.txt", "15 Jobs 3 Servers"),
        ("../results/september_4/mutate_iterative_auction_basic_j25_s5.txt", "25 Jobs 5 Servers")
    ]

    mutated_price_3_auction = [
        ("../results/september_5/mutate_iterative_auction_basic_j12_s2.txt", "12 Jobs 2 Servers"),
        ("../results/september_5/mutate_iterative_auction_basic_j15_s3.txt", "15 Jobs 3 Servers"),
        ("../results/september_5/mutate_iterative_auction_basic_j25_s5.txt", "25 Jobs 5 Servers")
    ]

    # plot_auction_results(normal_files, "Normal")
    # plot_auction_results(single_price_auctions, "Single Price")
    # plot_auction_results(multi_price_auction, "Multiple Price")

    plot_auction_results(mutated_price_auction, "Mutate")
    plot_auction_results(mutated_price_2_auction, "Mutate 2")
    plot_auction_results(mutated_price_3_auction, "Mutate 3")

    # print_multiple_auction_results(multi_price_auction)
    # print_mutated_auction_results(mutated_price_auction[0][0])
