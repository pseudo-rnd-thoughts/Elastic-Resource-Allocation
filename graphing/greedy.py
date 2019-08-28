
from __future__ import annotations
from typing import List, Dict

import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

from core.result import Result, AlgorithmResults


def plot_algorithms_results(results: List[Result]):
    """
    Plots the algorithm results with a plot for the total utility, percentage utility and percentage jobs
    :param results: A list of results
    """
    data = [[result.algorithm_name, result.sum_value, result.percentage_value, result.percentage_jobs]
            for result in results]

    df = pd.DataFrame(data, columns=['Algorithm Name', 'Total utility', 'Percentage utility', 'Percentage jobs'])
    df = pd.melt(df, id_vars=['Algorithm Name']).sort_values(['variable', 'value'])
    df.rename(columns={'variable': 'measure'}, inplace=True)

    g = sns.FacetGrid(df, col='measure', height=8, aspect=0.66, sharex=False)
    g.map(sns.barplot, 'value', 'Algorithm Name')

    plt.show()


def plot_repeat_algorithm_results(results: List[AlgorithmResults]):
    """
    Plots the repeat algorithm results for the total utility, percentage utility and percentage jobs
        of the mean and standard deviation
    :param results: A list of algorithm results
    """
    data = [[result.algorithm_name, 'total utility', utility]
            for result in results for utility in result.utility] + \
           [[result.algorithm_name, 'percentage utility', percentage_utility]
            for result in results for percentage_utility in result.percentage_utility] + \
           [[result.algorithm_name, 'percentage jobs', percentage_jobs]
            for result in results for percentage_jobs in result.percentage_jobs]

    df = pd.DataFrame(data, columns=['algorithm name', 'measure', 'value'])

    sns.barplot(y='algorithm name', x='value', col='measure',
                cut=0, height=6, aspect=0.1, data=df, orient='h', sharex=False)
    plt.show()


def plot_multi_models_results(model_results: Dict[str, List[AlgorithmResults]]):
    """
    Plot a multi model results
    :param model_results: The model results for all of the algorithms
    """
    data = [[model_name, result.algorithm_name, 'total utility', utility]
            for model_name, model_result in model_results.items()
            for result in model_result for utility in result.utility] + \
           [[model_name, result.algorithm_name, 'percentage utility', percentage_utility]
            for model_name, model_result in model_results.items()
            for result in model_result for percentage_utility in result.percentage_utility] + \
           [[model_name, result.algorithm_name, 'percentage jobs', percentage_jobs]
            for model_name, model_result in model_results.items()
            for result in model_result for percentage_jobs in result.percentage_jobs]

    df = pd.DataFrame(data, columns=['model name', 'algorithm name', 'measure', 'mean', 'std'])
    g = sns.FacetGrid(df, col='measure', height=4, aspect=4, sharey=False)
    g.map(sns.barplot, 'mean', 'model name', hue='algorithm name', orient='h')

    plt.xlabel('Test Name')
    plt.show()
