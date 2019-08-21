"""Optimality Testing"""

from core.model import load_dist, ModelDist

from optimal.optimal import optimal_algorithm
from optimal.mp_optimal import modified_mp_optimal_algorithm

if __name__ == "__main__":
    basic_dist_name, basic_job_dist, basic_server_dist = load_dist("../models/basic.model")
    basic_model_dist = ModelDist(basic_dist_name, basic_job_dist, 15, basic_server_dist, 3)
    jobs, servers = basic_model_dist.create()
    # optimal_algorithm(jobs, servers)
    modified_mp_optimal_algorithm(jobs, servers)

