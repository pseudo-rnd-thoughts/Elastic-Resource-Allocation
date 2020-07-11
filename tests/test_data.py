"""
Tests that the results data is valid
"""

import json
import os


def test_data_repeats():
    print(f'Filename - repeats')
    for filename in os.listdir('../data'):
        if '.json' in filename:
            with open(f'../data/{filename}') as file:
                data = json.load(file)
                print(f'{filename} - {len(data)}')
