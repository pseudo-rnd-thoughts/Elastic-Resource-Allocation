"""Auction mutation analysis"""

from __future__ import annotations

import json
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from core.core import decode_filename


def mutated_job_analysis(encoded_files: List[str]):
    """
    Analysis of the mutate job testing
    :param encoded_files: The files of different models
    """
    data = []
    for encoded_file in encoded_files:
        filename, model_name = decode_filename(encoded_file)
        with open(filename) as file:
            file_data = json.load(file)

            for pos, result in enumerate(file_data):
                for mutation_name, mutation_results in result.items():
                    if mutation_name == "no mutation":
                        data.append((pos, model_name, mutation_name, mutation_results['revenues'], 0, 0, 0,
                                     mutation_results['total_iterations']))
                    else:
                        data.append((pos, model_name, mutation_name, mutation_results['revenues'],
                                     mutation_results['mutant_value'], mutation_results['mutated_value'],
                                     mutation_results['mutant_value'] - mutation_results['mutated_value'],
                                     mutation_results['total_iterations']))

    df = pd.DataFrame(data, columns=['Pos', 'Model', 'Mutation', 'Revenue', 'Mutant Value', 'Mutated Value',
                                     'Mutate Difference', 'Iterations'])
    g = sns.FacetGrid(df, col='Model', col_wrap=2)
    # noinspection PyUnresolvedReferences
    (g.map(sns.scatterplot, 'Pos', 'Mutate Difference', hue='Mutation', data=df)
     .set_titles("{col_name}").set_xlabels("").add_legend())
    plt.show()
    """
    df = pd.DataFrame(data, columns=['model', 'pos', 'name', 'value', 'utility diff'])
    g: sns.FacetGrid = sns.FacetGrid(df, col='model', col_wrap=2)
    # noinspection PyUnresolvedReferences
    g = (g.map(sns.scatterplot, 'pos', 'utility diff', hue='name', data=df)
         .set_titles("{col_name}").set_xlabels("").add_legend())
    """


def all_mutation_analysis(files: List[str]):
    """
    Analysis of all mutations of job
    :param files: The files of the different models
    """
    for file in files:
        json.load(file)
    # TODO get the data
    pass


if __name__ == "__main__":
    # Old results for mutation is september 2, 4 and 5

    # Mutate jobs auction testing
    september_20 = [
        "september_20/mutate_iterative_auction_basic_j15_s_0.json"
    ]

    # All jobs mutation auction testing

    # Repeat testing
