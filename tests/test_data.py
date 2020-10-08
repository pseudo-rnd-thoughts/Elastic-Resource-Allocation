"""
Tests that the results data is valid
"""

import json
import os


def test_data_repeats():
    print(f'\nFilename - repeats')
    for filename in os.listdir('../data'):
        if '.json' in filename:
            with open(f'../data/{filename}') as file:
                data = json.load(file)
                print(f'{filename} - {len(data)}')

                if 'resource_ratio' in filename:
                    social_welfare = [result['social welfare'] for ratio, ratio_results in data[0].items()
                                      for algo, result in ratio_results.items() if ratio != 'model']
                elif 'batch_online' in filename:
                    social_welfare = [result['social welfare'] for algo, result in data[0].items()
                                      if algo != 'model' and 'length' not in algo]
                else:
                    social_welfare = [result['social welfare'] for algo, result in data[0].items() if algo != 'model']

                if all(social_welfare[0] == sw for sw in social_welfare):
                    print(f'[-] Social welfare is bugged ({filename})')


def test_optimal_data():
    print()
    for filename in os.listdir('../data/greedy'):
        with open(f'../data/greedy/{filename}') as file:
            data = json.load(file)

        if all('Flexible Optimal' in model for model in data):
            if all('solve status' in model['Flexible Optimal'] for model in data):
                flex_opt_percent = sum('Flexible Optimal' in model and 'solve status' in model['Flexible Optimal'] and
                                       model['Flexible Optimal']['solve status'] == 'Optimal' for model in data)
                relax_opt_percent = sum('Server Relaxed Flexible Optimal' in model and
                                        'solve status' in model['Server Relaxed Flexible Optimal'] and
                                        model['Server Relaxed Flexible Optimal']['solve status'] == 'Optimal'
                                        for model in data)

                print(f'{filename} - '
                      f'flexible: {flex_opt_percent / len(data):.3f}, '
                      f'relaxed: {relax_opt_percent / len(data):.3f}')
            else:
                print(f'{filename} - no solve status')
        else:
            print(f'{filename} - no flexible optimal')

    print()
    for filename in os.listdir('../data/auctions'):
        with open(f'../data/auctions/{filename}') as file:
            data = json.load(file)

        if all('Solve Status' in model for model in data):
            print(f'{filename}: solve status')
        else:
            print(f'{filename}: no solve status')
