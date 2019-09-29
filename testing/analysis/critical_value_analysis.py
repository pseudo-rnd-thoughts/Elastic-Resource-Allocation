"""Critical Value analysis"""

from __future__ import annotations

from typing import List

from core.core import decode_filename

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def critical_value_analysis(encoded_files: List[str]):
    """
    Analysis of the critical value analysis
    :param encoded_files: A list of encoded files to analysis
    """
    data = []

    for encoded_file in encoded_files:
        filename, model_name = decode_filename(encoded_file)
        with open(filename) as file:
            critical_value_data = json.load(file)

            for pos, result in enumerate(critical_value_data):
                for algorithm_name, critical_value_result in result.items():
                    data.append((model_name, pos, algorithm_name, critical_value_result['total money'],
                                 critical_value_result['value_density'],
                                 critical_value_result['server_selection_policy'],
                                 critical_value_result['resource_allocation_policy']))

    df = pd.DataFrame(data, columns=['Model', 'Pos', 'Algo Name', 'Total Money', 'Value Density',
                                     'Server Selection Policy', 'Resource Allocation Policy'])
    g = sns.FacetGrid(df, col='Model', col_wrap=2)
    # noinspection PyUnresolvedReferences
    (g.map(sns.scatterplot, 'Pos', 'Total Money', hue='Algo Name', data=df)
     .set_titles("{col_name}").set_xlabels("").add_legend())
    plt.show()


if __name__ == "__main__":
    september_20 = [
        "september_20/critical_value_results_basic_j12_s2_0.json",
        "september_20/critical_value_results_basic_j15_s2_0.json",
        "september_20/critical_value_results_basic_j15_s3_0.json",
        "september_20/critical_value_results_basic_j25_s5_0.json"
    ]
