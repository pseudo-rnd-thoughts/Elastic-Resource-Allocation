
import json


def auction_results(file):
    """
    Prints the Auction results from a file
    :param file: A file
    """
    with open(file) as json_file:
        data = json.load(json_file)

        print("Total utility for {}".format(file.split("/")[-1].split(".")[0]))
        for results in data:
            vcg = results['vcg'][0]
            iterative_results = {}
            for x in (1, 2, 3, 5, 7, 10):
                name = 'iterative {}'.format(x)
                if results[name][0] in iterative_results:
                    iterative_results[results[name][0]].append(str(x))
                else:
                    iterative_results[results[name][0]] = [str(x)]

            print("VCG: {:4d}, {}".format(vcg, ', '.join('e{}: {}'.format(' '.join(names), value)
                                                         for value, names in iterative_results.items())))
        print()


def plot_auction_results(file):
    with open(file) as json_file:
        json_data = json.load(json_file)


if __name__ == "__main__":
    _files = [
        "../results/23_august/auctions/auction_results_j12_s2.txt",
        "../results/23_august/auctions/auction_results_j15_s3.txt",
        "../results/23_august/auctions/auction_results_j25_s5.txt"
    ]
