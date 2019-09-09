"""A conversion script for json file to use with tableau"""

from __future__ import annotations

import json


def convert(file):
    """
    Converts a file to a tableau format
    :param file: The file to convert
    """
    with open(file) as json_file:
        data = json.load(json_file)

        converted_data = []
        for pos, line in enumerate(data):
            for name, results in line.items():
                converted_data.append({'pos': pos, 'name': name, 'results': results})

        new_file = "../" + file.strip('.txt') + '.json'
        with open(new_file, 'w') as new_json_file:
            json.dump(converted_data, new_json_file)


if __name__ == '__main__':
    optimal_greedy_test_basic = [
        ("../results/september_8/optimal_greedy_test_basic_j12_s2.txt", "12 Jobs 2 Servers"),
        ("../results/september_8/optimal_greedy_test_basic_j15_s3.txt", "15 Jobs 3 Servers"),
        ("../results/september_8/optimal_greedy_test_basic_j25_s5.txt", "25 Jobs 5 Servers")
    ]

    for test_file, model in optimal_greedy_test_basic:
        convert(test_file)
