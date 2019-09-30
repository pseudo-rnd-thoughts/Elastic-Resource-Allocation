"""Critical Value analysis"""

from __future__ import annotations

import json
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from core.core import decode_filename, save_plot


def critical_value_analysis(encoded_files: List[str], x_attribute: str = 'Total Money', save_filename: str = None):
    """
    Analysis of the critical value analysis
    :param encoded_files: A list of encoded files to analysis
    :param x_attribute: The x axis value
    :param save_filename: The save filename
    """
    data = []

    for encoded_file in encoded_files:
        filename, model_name = decode_filename(encoded_file)
        with open(filename) as file:
            critical_value_data = json.load(file)

            for pos, result in enumerate(critical_value_data):
                for algorithm_name, critical_value_result in result.items():
                    if algorithm_name == "price change 3":
                        data.append((model_name, pos, "Iterative Auction", critical_value_result['total money'],
                                     "", "", "", critical_value_result['solve_time']))
                    else:
                        data.append((model_name, pos, algorithm_name, critical_value_result['total money'],
                                     critical_value_result['value_density'],
                                     critical_value_result['server_selection_policy'],
                                     critical_value_result['resource_allocation_policy'],
                                     critical_value_result['solve_time']))

    df = pd.DataFrame(data, columns=['Model', 'Pos', 'Algorithm Name', 'Total Money', 'Value Density',
                                     'Server Selection Policy', 'Resource Allocation Policy', 'Solve Time'])

    g = sns.FacetGrid(df, col='Model', height=6, sharex=False)
    g: sns.FacetGrid = (g.map(sns.barplot, x_attribute, 'Algorithm Name', ci=95, data=df)
                        .set_titles("{col_name}"))
    """
    g = sns.FacetGrid(df, col='Model', col_wrap=2)
    # noinspection PyUnresolvedReferences
    (g.map(sns.scatterplot, 'Pos', 'Total Money', hue='Algo Name', data=df)
     .set_titles("{col_name}").set_xlabels("").add_legend())
     """
    if save_filename is not None:
        save_plot(save_filename)
    plt.show()


if __name__ == "__main__":
    # No old results
    september_20 = [
        "september_20/critical_values_results_basic_j12_s2_0",
        "september_20/critical_values_results_basic_j15_s2_0",
        "september_20/critical_values_results_basic_j15_s3_0",
        "september_20/critical_values_results_basic_j25_s5_0"
    ]

    critical_value_analysis(september_20, "critical_value")
