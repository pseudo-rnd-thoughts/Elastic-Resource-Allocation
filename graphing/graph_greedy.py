"""Graphs the greedy algorithms"""

from __future__ import annotations

from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from core.result import Result


def plot_algorithms_results(results: List[Result]):
    """
    Plots the algorithm results with a plot for the total utility, percentage utility and percentage jobs
    :param results: A list of results
    """
    data = [[result.algorithm_name, result.sum_value, result.data['percentage value'], result.data['percentage jobs']]
            for result in results]

    df = pd.DataFrame(data, columns=['Algorithm Name', 'Total utility', 'Percentage utility', 'Percentage jobs'])
    df = pd.melt(df, id_vars=['Algorithm Name']).sort_values(['variable', 'value'])
    df.rename(columns={'variable': 'measure'}, inplace=True)

    g = sns.FacetGrid(df, col='measure', height=8, aspect=0.66, sharex=False)
    g.map(sns.barplot, 'value', 'Algorithm Name')

    plt.show()
