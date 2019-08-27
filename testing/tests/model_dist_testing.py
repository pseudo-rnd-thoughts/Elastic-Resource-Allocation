"""Model Distribution Testing"""

from core.model import load_dist, ModelDist
import graphing.plot_model as graphing


def plot_distributions():
    """
    Plot the job and server distributions
    """
    basic_dist_name, basic_job_dist, basic_server_dist = load_dist("../models/basic.model")
    basic_model_dist = ModelDist(basic_dist_name, basic_job_dist, 10, basic_server_dist, 10)
    
    bs_dist_name, bs_job_dist, bs_server_dist = load_dist("../models/big_small.model")
    bs_model_dist = ModelDist(bs_dist_name, bs_job_dist, 10, bs_server_dist, 10)
    
    graphing.plot_job_distribution([basic_model_dist, bs_model_dist])
    graphing.plot_server_distribution([basic_model_dist, bs_model_dist])


if __name__ == "__main__":
    plot_distributions()
