"""Price Change analysis"""

from __future__ import annotations

import json
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from core.core import decode_filename, save_plot


def plot_auction_results(encoded_files: List[str], save_filename: str = None):
    """
    Plots the auction results
    :param encoded_files: The list of encoded files
    """
    data = []
    for encoded_file in encoded_files:
        filename, model_name = decode_filename(encoded_file)
        with open(filename) as json_file:
            json_data = json.load(json_file)

            for pos, results in enumerate(json_data):
                for name, result in results.items():
                    data.append((model_name, pos, name, result[0], result[1]))
    data = reversed(data)

    df = pd.DataFrame(data, columns=['model', 'pos', 'name', 'value', 'price'])
    g: sns.FacetGrid = sns.FacetGrid(df, col='model', col_wrap=2)
    # noinspection PyUnresolvedReferences
    (g.map(sns.scatterplot, 'pos', 'value', hue='name', data=df)
     .set_titles("{col_name}").add_legend())

    if save_filename is not None:
        save_plot(save_filename)
    plt.show()


def plot_multiple_price_auction_results(files):
    """
    Plots the auction results
    :param files: The files
    """
    data = []
    for file, model in files:
        with open(file) as json_file:
            json_data = json.load(json_file)

            for pos, results in enumerate(json_data):
                for name, result in results.items():
                    if name == "price change 1 1" or name == "price change 1 1 1":
                        data.append((model, pos, "standard", result[0], result[1]))
                    else:
                        data.append((model, pos, "changed", result[0], result[1]))
    data = reversed(data)

    df = pd.DataFrame(data, columns=['model', 'pos', 'name', 'value', 'price'])
    g: sns.FacetGrid = sns.FacetGrid(df, col='model', col_wrap=2)
    # noinspection PyUnresolvedReferences
    (g.map(sns.scatterplot, 'pos', 'value', hue='name', data=df)
     .set_titles("{col_name}").add_legend())
    plt.show()


if __name__ == "__main__":
    # Old results in august 26 and 30

    september_20 = [
        "september_20/"
    ]
