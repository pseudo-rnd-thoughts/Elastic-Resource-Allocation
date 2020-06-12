"""A conversion script for json file to use with tableau"""

from __future__ import annotations

import json
import csv


def csv_convert(file: str):
    """
    Convert the file to a CSV file
    :param file: The file location
    """
    with open(file) as original_file:
        data = json.load(original_file)

        new_file = file.strip('.txt') + '.csv'
        with open(new_file, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter='', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            
            for pos, line in enumerate(data):
                for name, results in line.items():
                    new_line = [pos, name]
                    for _, result in results.items():
                        new_line.append(result)
                        
                    csv_writer.writerow(new_line)
                    

def json_convert(file):
    """
    Converts a file to a tableau format
    :param file: The file to convert
    """
    with open(file) as original_file:
        data = json.load(original_file)

        converted_data = []
        for pos, line in enumerate(data):
            for name, results in line.items():
                converted_data.append({'pos': pos, 'name': name, 'results': results})

        new_file = "../" + file.strip('.txt') + '.json'
        with open(new_file, 'w') as new_json_file:
            json.dump(converted_data, new_json_file)


if __name__ == '__main__':
    optimal_greedy_test_basic = [
        ("../results/september_8/optimal_greedy_test_basic_j12_s2.txt", "12 Tasks 2 Servers"),
        ("../results/september_8/optimal_greedy_test_basic_j15_s3.txt", "15 Tasks 3 Servers"),
        ("../results/september_8/optimal_greedy_test_basic_j25_s5.txt", "25 Tasks 5 Servers")
    ]

    for test_file, model in optimal_greedy_test_basic:
        json_convert(test_file)
