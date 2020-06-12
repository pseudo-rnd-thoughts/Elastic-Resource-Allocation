"""Price Change analysis"""

from __future__ import annotations

import json
from typing import List, Iterable

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.core.core import decode_filename, save_plot, analysis_filename, ImageFormat

matplotlib.rcParams['font.family'] = 'monospace'


def plot_auction_results(encoded_filenames: List[str], y_axis: str, title: str,
                         save_formats: Iterable[ImageFormat] = ()):
    """
    Plots the auction results

    :param encoded_filenames: The list of encoded filenames
    :param y_axis: The y axis on the plot
    :param title: The graph titles
    :param save_formats: List of save formats
    """
    data = []
    test_name: str = ''
    model_names: List[str] = []

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename('paper', encoded_filename)
        model_names.append(model_name)

        with open(filename) as json_file:
            json_data = json.load(json_file)

            for pos, results in enumerate(json_data):
                for name, result in results.items():
                    if type(result) is dict:
                        data.append((model_name, pos, name, result['sum value'], result['total money'],
                                     result['total money'] / results['price change 1']['total money'],
                                     result['solve_time']))
    data = reversed(data)

    df = pd.DataFrame(data, columns=['Model Name', 'Pos', 'Algorithm Name', 'Sum Value', 'Total Money',
                                     'Best Total Money', 'Solve Time'])
    g: sns.FacetGrid = sns.FacetGrid(df, col='Model Name', hue='Algorithm Name')
    g = (g.map(sns.scatterplot, 'Pos', y_axis).set_titles('{col_name}').add_legend())

    g.fig.subplots_adjust(top=0.88)
    g.fig.suptitle(title)

    save_plot(analysis_filename(test_name, y_axis), 'price_change', image_formats=save_formats)
    plt.show()


def plot_multiple_price_auction_results(encoded_filenames: List[str], y_axis: str, title: str,
                                        save_formats: Iterable[ImageFormat] = ()):
    """
    Plots the auction results

    :param encoded_filenames: A list of encoded filenames
    :param y_axis: The y axis on the plot
    :param title: The graph title
    :param save_formats: List of save formats
    """
    data = []
    test_name: str = ''
    model_names: List[str] = []

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename('price_change', encoded_filename)
        model_names.append(model_name)

        with open(filename) as file:
            json_data = json.load(file)

            for pos, results in enumerate(json_data):
                for name, result in results.items():
                    if type(result) is dict:
                        data.append((pos, model_name, 'changed', result['sum value'], result['total money'],
                                     result['solve_time']))
    data = reversed(data)

    df = pd.DataFrame(data, columns=['Pos', 'Model Name', 'Algorithm Name', 'Sum Value', 'Total Money', 'Solve Time'])
    g: sns.FacetGrid = sns.FacetGrid(df, col='Model Name', hue='Algorithm Name')
    (g.map(sns.scatterplot, 'Pos', y_axis).set_titles('{col_name}'))

    g.fig.subplots_adjust(top=0.88)
    g.fig.suptitle(title)

    save_plot(analysis_filename(test_name, y_axis), 'price_change', image_formats=save_formats)
    plt.show()


if __name__ == "__main__":
    # Old results in august 26 and 30
    uniform = [
        'uniform_price_change_auction_results_basic_j15_s2_0',
        'uniform_price_change_auction_results_basic_j15_s3_0',
        'uniform_price_change_auction_results_basic_j25_s5_0'
    ]

    non_uniform = [
        'non_uniform_price_change_auction_results_basic_j12_s2_0',
        # 'non_uniform_price_change_auction_results_basic_j15_s2_0',
        'non_uniform_price_change_auction_results_basic_j15_s3_0',
        'non_uniform_price_change_auction_results_basic_j25_s5_0'
    ]

    paper = [
        'uniform_price_change_auction_results_fog_j15_s3_0'
    ]

    plot_auction_results(paper, 'Sum Value', 'Sum Value', save_formats=[ImageFormat.EPS, ImageFormat.PNG])
    plot_auction_results(paper, 'Total Money', 'Total Money', save_formats=[ImageFormat.EPS, ImageFormat.PNG])
    plot_auction_results(paper, 'Solve Time', 'Solve Time', save_formats=[ImageFormat.EPS, ImageFormat.PNG])

    """
    for attribute in ['Sum Value', 'Total Money', 'Solve Time']:
        plot_auction_results(uniform, attribute, '{} of uniform basic model'.format(attribute),
                             save_formats=[ImageFormat.EPS, ImageFormat.PNG])
        plot_multiple_price_auction_results(non_uniform, attribute, '{} of non uniform basic model'.format(attribute),
                                            save_formats=[ImageFormat.EPS, ImageFormat.PNG])
    plot_auction_results(uniform, 'Best Total Money', '{} of uniform basic model'.format('Best Total Money'),
                         save_formats=[ImageFormat.EPS, ImageFormat.PNG])
    """
