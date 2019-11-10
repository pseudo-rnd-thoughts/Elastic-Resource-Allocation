"""Branch & Bound algorithm"""
from typing import List, Tuple, Dict

from branch_bound.branch_bound import branch_bound_algorithm, generate_candidates, print_allocation
from core.core import load_args
from core.job import Job
from core.model import ModelDist, load_dist
from core.server import Server


def branch_bound_test(model_dist: ModelDist):
    jobs, servers = model_dist.create()
    
    result = branch_bound_algorithm(jobs, servers)
    print(result.store())
    

def test_candidates(model_dist: ModelDist):
    jobs, servers = model_dist.create()

    candidates: List[Tuple[float, float, Dict[Server, List[Job]], int]] = generate_candidates(
        {server: [] for server in servers}, jobs[0], servers, 1, 0, sum(job.value for job in jobs), 0)
    
    for candidate in candidates:
        print(candidate)


if __name__ == "__main__":
    args = load_args()

    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])
    
    branch_bound_test(loaded_model_dist)
    # test_candidates(loaded_model_dist)
