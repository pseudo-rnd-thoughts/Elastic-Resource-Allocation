"""Plots the auction results"""

from __future__ import annotations

import json
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from core.server import Server
from graphing.plot_model import plot_allocation_results


def mean_std_results(files):
    """
    Prints the mean and stardard deviation of the file results
    :param files: A list of files
    """
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


# noinspection DuplicatedCode
def plot_auction_result(servers: List[Server], name: str):
    """
    Plots the server jobs allocations
    :param servers: A list of servers to plot
    :param name: For the auctions name
    """
    server_names = [server.name for server in servers]
    allocated_jobs = [job for server in servers for job in server.allocated_jobs]
    job_names = [job.name for job in allocated_jobs]
    storage_df = pd.DataFrame([[job.required_storage / server.max_storage if job in server.allocated_jobs else 0
                                for job in allocated_jobs] for server in servers],
                              index=server_names, columns=job_names)
    compute_df = pd.DataFrame([[job.compute_speed / server.max_computation if job in server.allocated_jobs else 0
                                for job in allocated_jobs] for server in servers],
                              index=server_names, columns=job_names)
    bandwidth_df = pd.DataFrame([[(job.loading_speed + job.sending_speed) / server.max_bandwidth
                                  if job in server.allocated_jobs else 0
                                  for job in allocated_jobs] for server in servers],
                                index=server_names, columns=job_names)
    price_df = pd.DataFrame([[job.price/server.revenue if job in server.allocated_jobs else 0
                              for job in allocated_jobs] for server in servers],
                            index=server_names, columns=job_names)
    print(price_df)

    df_all = [storage_df, compute_df, bandwidth_df, price_df]
    labels = ['storage', 'compute', 'bandwidth', 'price']
    title = '{} Auction Allocation'.format(name)

    plot_allocation_results(df_all, title, labels, "Servers", "Percentage of Server resources")


def plot_auction_convergence(auctions_utilities: Dict[str, List[float]], auctions_prices: Dict[str, List[float]],
                             vcg_utility: float, vcg_price: float):
    """
    Plots the auctions utility and revenue as it convergence
    :param auctions_utilities: A dictionary of auctions utility with auctions name
    :param auctions_prices: A dictionary of auctions prices with auctions name
    :param vcg_utility: The vcg utility
    :param vcg_price:  The vcg price
    """
    max_iterations = max(len(auction_prices) for auction_prices in auctions_prices.values())

    data = [['price', auction, pos, auction_price] for auction, auction_prices in auctions_prices.items()
            for pos, auction_price in enumerate(auction_prices)] + \
           [['utility', auction, pos, auction_utility] for auction, auction_utilities in auctions_utilities.items()
            for pos, auction_utility in enumerate(auction_utilities)]

    for pos in range(max_iterations):
        data.append(['price', 'vcg', pos, vcg_price])
        data.append(['utility', 'vcg', pos, vcg_utility])
    df = pd.DataFrame(data, columns=['measure', 'auctions name', 'time', 'utility'])

    sns.lineplot('time', 'utility', hue='auctions name', data=df, row='measure')
    plt.title("Auction Utility Convergence")
    plt.show()
