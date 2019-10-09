"""Critical Value analysis"""

from __future__ import annotations

import json
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from core.core import decode_filename, save_plot, analysis_filename


def critical_value_analysis(encoded_filenames: List[str], x_axis: str, title: str, save: bool = False):
    """
    Analysis of the critical value analysis
    :param encoded_filenames: The list of encoded filenames
    :param x_axis: The x axis to plot
    :param save: The save filename
    """
    data = []
    test_name: str = ""

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename('critical_value', encoded_filename)
        with open(filename) as file:
            critical_value_data = json.load(file)

            for pos, result in enumerate(critical_value_data):
                for algorithm_name, critical_value_result in result.items():
                    if algorithm_name == "price change 3":
                        data.append((model_name, pos, "Iterative Auction", critical_value_result['total money'],
                                     "", "", "", critical_value_result['solve_time']))
                    else:
                        data.append((model_name, pos, algorithm_name,
                                     critical_value_result['total money'],
                                     critical_value_result['value_density'],
                                     critical_value_result['server_selection_policy'],
                                     critical_value_result['resource_allocation_policy'],
                                     critical_value_result['solve_time']))

    df = pd.DataFrame(data, columns=['Model', 'Pos', 'Algorithm Name', 'Total Money', 'Value Density',
                                     'Server Selection Policy', 'Resource Allocation Policy', 'Solve Time'])

    g = sns.FacetGrid(df, col='Model', height=6, sharex=False)
    g: sns.FacetGrid = (g.map(sns.barplot, x=x_axis, y='Algorithm Name', data=df).set_titles("{col_name}"))

    g.fig.suptitle(title)

    if save:
        save_plot(analysis_filename(test_name, x_axis), "critical_value")
    plt.show()


if __name__ == "__main__":
    # No old results

    september_20 = [
        "critical_values_results_basic_j12_s2_0",
        "critical_values_results_basic_j15_s2_0",
        "critical_values_results_basic_j15_s3_0",
        "critical_values_results_basic_j25_s5_0"
    ]

    for attribute in ['Total Money', 'Solve Time']:
        critical_value_analysis(september_20, attribute, '{} of basic model'.format(attribute), save=True)
