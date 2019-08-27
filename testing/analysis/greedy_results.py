
import json
import numpy as np


def algo_optimal_difference(file):
    with open(file) as json_file:
        data = json.load(json_file)

        results_difference = {}
        sub_optimal = 0

        for results in data:
            optimal = results['Optimal']
            max_algo = max(value for value in results.values())
            if max_algo > optimal:
                sub_optimal += 1
                print("Optimal: {:3.0f}, Max: {:3.0f} by {}".format(optimal, max_algo, max((algo for algo in results),
                                                                                           key=lambda x: results[x])))
                continue
            for result, value in results.items():
                if result in results_difference:
                    results_difference[result].append(optimal - value)
                else:
                    results_difference[result] = [optimal - value]

        print("Number of suboptimal is {} of {}".format(sub_optimal, len(data)))
        print()
        for algo, difference in results_difference.items():
            print("Mean: {:6.3f}, Std: {:6.3f} - {}".format(np.mean(difference), np.std(difference), algo))


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
        print("{} has {} sub optimal solution of {}".format(file.split("/")[-1].split(".")[0], sub_optimal, total[file]))
    print()

    for algo, percent_difference in sorted(algo_difference.items(), key=lambda x: np.mean(x[1]), reverse=True):
        print("Mean: {:6.3f}, Std: {:6.3f} - {}".format(np.mean(percent_difference), np.std(percent_difference), algo))


if __name__ == "__main__":
    # algo_optimal_difference("../results/results_26_august/greedy_results_j12_s2.txt")
    algo_optimal_percent_difference([
        "../results/results_26_august/greedy/greedy_results_j12_s2.txt",
        "../results/results_26_august/greedy/greedy_results_j15_s3.txt"
    ])
