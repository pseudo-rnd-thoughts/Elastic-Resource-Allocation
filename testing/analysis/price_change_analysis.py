"""Price Change analysis"""

from __future__ import annotations

import json
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from core.core import decode_filename, save_plot, analysis_filename

matplotlib.rcParams['font.family'] = "monospace"


def plot_auction_results(encoded_filenames: List[str], y_axis: str, save: bool = False):
    """
    Plots the auction results
    :param encoded_filenames: The list of encoded filenames
    :param y_axis: The y axis on the plot
    :param save: If to save the plot
    """
    data = []
    test_name: str = ""

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename(encoded_filename)
        with open(filename) as json_file:
            json_data = json.load(json_file)

            for pos, results in enumerate(json_data):
                for name, result in results.items():
                    data.append((model_name, pos, name, result[0], result[1]))
    data = reversed(data)

    df = pd.DataFrame(data, columns=['model', 'pos', 'name', 'value', 'price'])
    g: sns.FacetGrid = sns.FacetGrid(df, col='model', col_wrap=2)
    # noinspection PyUnresolvedReferences
    (g.map(sns.scatterplot, x='pos', y=y_axis, hue='name').set_titles("{col_name}").add_legend())

    if save:
        save_plot(analysis_filename(test_name, y_axis))
    plt.show()


def plot_multiple_price_auction_results(encoded_filenames: List[str], y_axis: str, save: bool = False):
    """
    Plots the auction results
    :param encoded_filenames: A list of encoded filenames
    :param y_axis: The y axis on the plot
    :param save: If to save the plot
    """
    data = []
    test_name: str = ""

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename(encoded_filename)
        with open(filename) as json_file:
            json_data = json.load(json_file)

            for pos, results in enumerate(json_data):
                for name, result in results.items():
                    if name == "price change 1 1" or name == "price change 1 1 1":
                        data.append((model_name, pos, "standard", result[0], result[1]))
                    else:
                        data.append((model_name, pos, "changed", result[0], result[1]))
    data = reversed(data)

    df = pd.DataFrame(data, columns=['model', 'pos', 'name', 'value', 'price'])
    g: sns.FacetGrid = sns.FacetGrid(df, col='model', col_wrap=2)
    # noinspection PyUnresolvedReferences
    (g.map(sns.scatterplot, 'pos', 'value', hue='name', data=df).set_titles("{col_name}").add_legend())

    if save:
        save_plot(analysis_filename(test_name, y_axis))
    plt.show()


if __name__ == "__main__":
    # Old results in august 26 and 30

    september_20 = [
        "september_20/"
    ]
