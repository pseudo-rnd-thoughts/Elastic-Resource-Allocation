"""Critical Value analysis"""

from __future__ import annotations

import json
from typing import List, Iterable

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

from core.core import decode_filename, save_plot, analysis_filename, ImageFormat


def critical_value_analysis(encoded_filenames: List[str], x_axis: str, title: str,
                            save_formats: Iterable[ImageFormat] = ()):
    """
    Analysis of the critical value analysis
    :param encoded_filenames: The list of encoded filenames
    :param x_axis: The x axis to plot
    :param title: The title of the graph
    :param save_formats: List of save formats
    """
    data = []
    test_name: str = ""
    model_names: List[str] = []

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename('critical_value', encoded_filename)
        model_names.append(model_name)

        with open(filename) as file:
            critical_value_data = json.load(file)

            for pos, result in enumerate(critical_value_data):
                for algorithm_name, critical_value_result in result.items():
                    if algorithm_name == "price change 3":
                        data.append((model_name, pos, "Iterative Auction", critical_value_result['total money'], 1,
                                     "", "", "", critical_value_result['solve_time']))
                    else:
                        data.append((model_name, pos, algorithm_name,
                                     critical_value_result['total money'],
                                     critical_value_result['total money'] / result['price change 3']['total money'],
                                     critical_value_result['value_density'],
                                     critical_value_result['server_selection_policy'],
                                     critical_value_result['resource_allocation_policy'],
                                     critical_value_result['solve_time']))

    df = pd.DataFrame(data, columns=['Model', 'Pos', 'Algorithm Name', 'Total Money', 'Best Total Money',
                                     'Value Density', 'Server Selection Policy', 'Resource Allocation Policy',
                                     'Solve Time'])

    g = sns.FacetGrid(df, col='Model', height=6, sharex=False)
    g: sns.FacetGrid = (g.map(sns.barplot, x_axis, 'Algorithm Name').set_titles("{col_name}"))

    for pos, model in enumerate(model_names):
        values = [np.mean(df[(df['Model'] == model) & (df['Algorithm Name'] == algo)][x_axis])
                  for algo in df['Algorithm Name'].unique()]
        g.axes[0, pos].set_xlim(min(values) * 0.97, max(values) * 1.02)

    g.fig.subplots_adjust(top=0.92)
    g.fig.suptitle(title)

    save_plot(analysis_filename(test_name, x_axis), "critical_value", image_formats=save_formats)
    plt.show()


if __name__ == "__main__":
    # No old results

    basic = [
        "critical_values_results_basic_j12_s2_0",
        # "critical_values_results_basic_j15_s2_0",
        "critical_values_results_basic_j15_s3_0",
        "critical_values_results_basic_j25_s5_0"
    ]

    for attribute in ['Total Money', 'Best Total Money', 'Solve Time']:
        critical_value_analysis(basic, attribute, '{} of Basic model'.format(attribute),
                                save_formats=[ImageFormat.EPS, ImageFormat.PNG])
