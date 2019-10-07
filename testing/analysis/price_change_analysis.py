"""Price Change analysis"""

from __future__ import annotations

import json
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from core.core import decode_filename, save_plot, analysis_filename, save_eps

matplotlib.rcParams['font.family'] = "monospace"


def plot_auction_results(encoded_filenames: List[str], y_axis: str, title: str, save: bool = False):
    """
    Plots the auction results
    :param encoded_filenames: The list of encoded filenames
    :param y_axis: The y axis on the plot
    :param save: If to save the plot
    """
    data = []
    test_name: str = ""

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename('price_change', encoded_filename)
        with open(filename) as json_file:
            json_data = json.load(json_file)

            for pos, results in enumerate(json_data):
                for name, result in results.items():
                    if type(result) is dict:
                        data.append((model_name, pos, name, result['sum value'], result['total money']))
    data = reversed(data)

    df = pd.DataFrame(data, columns=['model', 'pos', 'name', 'value', 'price'])
    g: sns.FacetGrid = sns.FacetGrid(df, col='model', col_wrap=2)
    # noinspection PyUnresolvedReferences
    g = (g.map(sns.scatterplot, x='pos', y=y_axis, hue='name', data=df).set_titles("{col_name}").add_legend())

    print(plt.gcf(), g.fig)

    g.fig.suptitle(title)

    if save:
        save_plot(analysis_filename(test_name, y_axis))
    plt.show()


def plot_multiple_price_auction_results(encoded_filenames: List[str], y_axis: str, title: str, save: bool = False):
    """
    Plots the auction results
    :param encoded_filenames: A list of encoded filenames
    :param y_axis: The y axis on the plot
    :param save: If to save the plot
    """
    data = []
    test_name: str = ""

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename('price_change', encoded_filename)
        with open(filename) as file:
            json_data = json.load(file)

            for pos, results in enumerate(json_data):
                for name, result in results.items():
                    if type(result) is dict:
                        if name == "price change 1 1" or name == "price change 1 1 1":
                            data.append((pos, model_name, "standard", result['sum value'], result['total money']))
                        else:
                            data.append((pos, model_name, "changed", result['sum value'], result['total money']))
    data = reversed(data)

    df = pd.DataFrame(data, columns=['Pos', 'Model Name', 'Algorithm Name', 'Value', 'Price'])
    g: sns.FacetGrid = sns.FacetGrid(df, col='Model Name', col_wrap=2)
    # noinspection PyUnresolvedReferences
    (g.map(sns.scatterplot, x='Pos', y='Value', hue='Algorithm Name', data=df).set_titles("{col_name}").add_legend())

    g.fig.suptitle(title)

    if save:
        save_plot(analysis_filename(test_name, y_axis))
    plt.show()


if __name__ == "__main__":
    # Old results in august 26 and 30
    save_eps = False

    uniform = [
        "uniform_price_change_auction_results_basic_j15_s2_0",
        "uniform_price_change_auction_results_basic_j15_s3_0",
        "uniform_price_change_auction_results_basic_j25_s5_0"
    ]

    non_uniform = [
        "non_uniform_price_change_auction_results_basic_j12_s2_0",
        "non_uniform_price_change_auction_results_basic_j15_s2_0",
        "non_uniform_price_change_auction_results_basic_j15_s3_0",
        "non_uniform_price_change_auction_results_basic_j25_s5_0"
    ]

    for attribute in ['price']:
        plot_auction_results(uniform, attribute, '{} of uniform basic model'.format(attribute))
        plot_multiple_price_auction_results(uniform, attribute, '{} of non uniform basic model'.format(attribute),
                                            save=True)
