"""Auction mutation analysis"""

from __future__ import annotations

import json
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from core.core import decode_filename, save_plot, analysis_filename, ImageFormat


def mutated_job_analysis(encoded_filenames: List[str], y_axis: str, title: str,
                         save_format: ImageFormat = ImageFormat.NONE):
    """
    Analysis of the mutate job testing
    :param encoded_filenames: A list of encoded filenames
    :param y_axis: The y axis on the plot
    :param title: The title of the plot
    :param save_format: The save format
    """
    data = []
    test_name: str = ""

    for encoded_filename in encoded_filenames:
        filename, model_name, test_name = decode_filename("auction_mutation", encoded_filename)
        with open(filename) as file:
            file_data = json.load(file)

            for pos, result in enumerate(file_data):
                for mutation_name, mutation_results in result.items():
                    if mutation_name == "no mutation":
                        data.append((pos, model_name, "No Mutation", mutation_results['revenues'], 0, 0, 0,
                                     mutation_results['total_iterations']))
                    else:
                        if mutation_results['mutant_value'] - mutation_results['mutated_value'] > 0:
                            print(mutation_results)
                        data.append((pos, model_name, "Mutation", mutation_results['revenues'],
                                     mutation_results['mutant_value'], mutation_results['mutated_value'],
                                     mutation_results['mutant_value'] - mutation_results['mutated_value'],
                                     mutation_results['total_iterations']))
    data = reversed(data)

    df = pd.DataFrame(data, columns=['Pos', 'Model', 'Mutation', 'Revenue', 'Mutant Value', 'Mutated Value',
                                     'Mutate Difference', 'Iterations'])

    g = sns.FacetGrid(df, col='Model', col_wrap=2, hue='Mutation')
    g = (g.map(sns.scatterplot, 'Pos', y_axis)
         .set_titles("{col_name}").set_xlabels("").add_legend())
    plt.legend(loc='bottom', bbox_to_anchor=(1, 0.5))

    g.fig.subplots_adjust(top=0.88)
    g.fig.suptitle(title)

    save_plot(analysis_filename(test_name, y_axis), "auction_mutation", image_format=save_format)
    plt.show()


if __name__ == "__main__":
    # Old results for mutation is september 2, 4 and 5

    # Mutate jobs auction testing
    mutate_september_20 = [
        "mutate_iterative_auction_basic_j12_s2_0",
        "mutate_iterative_auction_basic_j15_s2_0",
        "mutate_iterative_auction_basic_j15_s3_0",
        "mutate_iterative_auction_basic_j25_s5_0"
    ]
    mutated_job_analysis(mutate_september_20, 'Mutate Difference', 'Effect of job misrepresentation on prices',
                         save_format=ImageFormat.BOTH)

    # All jobs mutation auction testing

    # Repeat testing
