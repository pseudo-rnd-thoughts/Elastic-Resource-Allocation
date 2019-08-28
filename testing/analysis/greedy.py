
import json
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd


def algo_optimal_percent_difference(files):
    algo_difference = {}
    sub_optimals = {}
    total = {}
    for file in files:
        with open(file) as json_file:
            data = json.load(json_file)

            total[file] = len(data)
            for results in data:
                optimal = results['Optimal']
                max_algo = max(((value, algo) for algo, value in results.items()), key=lambda x: x[0])

                if max_algo[0] > optimal:
                    if file in sub_optimals:
                        sub_optimals[file] += 1
                    else:
                        sub_optimals[file] = 1
                    continue

                for result, value in results.items():
                    if result in algo_difference:
                        algo_difference[result].append(value / optimal)
                    else:
                        algo_difference[result] = [value / optimal]

    for file, sub_optimal in sub_optimals.items():
        print("{} has {} sub optimal solution of {}"
              .format(file.split("/")[-1].split(".")[0], sub_optimal, total[file]))
    print()

    for algo, percent_difference in sorted(algo_difference.items(), key=lambda x: np.mean(x[1]), reverse=True):
        print("Mean: {:6.3f}, Std: {:6.3f} - {}".format(np.mean(percent_difference), np.std(percent_difference), algo))


def plot_results(file):
    """
    Plots the results from a file
    :param file: A file of results
    """
    algo_difference = {}
    with open(file) as json_file:
        data = json.load(json_file)
    
        for results in data:
            optimal = results['Optimal']
        
            for result, value in results.items():
                if result in algo_difference:
                    algo_difference[result].append(value / optimal)
                else:
                    algo_difference[result] = [value / optimal]
    
    algo_difference['Optimal'] = [100]
    data = [(algo, np.mean(percent_difference))
            for algo, percent_difference in sorted(algo_difference.items(), key=lambda x: np.mean(x[1]))]
    df = pd.DataFrame(data, columns=['algorithm', 'value'])
    sns.barplot('algorithm', 'value', data=df, orient='h')
    plt.show()
    

if __name__ == "__main__":
    """
    algo_optimal_percent_difference([
        "../results/results_26_august/greedy/greedy_results_j12_s2.txt",
        "../results/results_26_august/greedy/greedy_results_j15_s3.txt"
    ])
    """
    plot_results("../results/results_26_august/greedy/greedy_results_j12_s2.txt")
