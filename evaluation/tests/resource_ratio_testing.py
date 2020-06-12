import json

from tqdm import tqdm

from core import load_args, results_filename
from core import FixedJob, FixedSumSpeeds
from core import load_dist, ModelDist, reset_model
from greedy.greedy import greedy_algorithm
from greedy import SumPercentage, SumSpeed
from greedy import SumResources, JobSumResources
from greedy import UtilityPerResources, UtilityResourcePerDeadline, UtilityDeadlinePerResource, Value
from optimal.fixed_optimal import fixed_optimal_algorithm
from optimal import optimal_algorithm


def resource_ratio_testing(model_dist: ModelDist, repeat: int, repeats: int = 10):
    data = []
    for _ in tqdm(range(repeats)):
        results = {}
        jobs, servers = model_dist.create()
        fixed_jobs = [FixedJob(job, FixedSumSpeeds()) for job in jobs]
        
        total_resources = {server: server.computation_capacity + server.bandwidth_capacity for server in servers}
        for ratio in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
            ratio_results = {}
            for server in servers:
                server.update_capacities(int(total_resources[server] * ratio),
                                         int(total_resources[server] * (1 - ratio)))
                
            optimal_results = optimal_algorithm(jobs, servers, 180)
            ratio_results['optimal'] = optimal_results.store(ratio=ratio,
                server_ratio={server: server.computation_capacity / server.bandwidth_capacity for server in servers})
            
            reset_model(jobs, servers)
            
            fixed_results = fixed_optimal_algorithm(fixed_jobs, servers, 180)
            ratio_results['fixed'] = fixed_results.store(ratio=ratio,
                server_ratio={server: server.computation_capacity / server.bandwidth_capacity for server in servers})
            
            reset_model(jobs, servers)
            
            greedy_policies = [
                (vd, ss, ra)
                for vd in [UtilityPerResources(), UtilityResourcePerDeadline(), UtilityDeadlinePerResource(), Value()]
                for ss in [SumResources(), SumResources(True),
                           JobSumResources(SumPercentage()), JobSumResources(SumPercentage(), True),
                           JobSumResources(SumSpeed()), JobSumResources(SumSpeed(), True)]
                for ra in [SumPercentage(), SumSpeed()]
            ]
            for (vd, ss, ra) in greedy_policies:
                try:
                    greedy_result = greedy_algorithm(jobs, servers, vd, ss, ra)
                    ratio_results[greedy_result.algorithm_name] = greedy_result.store()
                except Exception as e:
                    print(e)

                reset_model(jobs, servers)

            results['ratio {}'.format(ratio)] = ratio_results
        data.append(results)
        
        # Save the results to the file
        filename = results_filename('resource_ratio', model_dist.file_name, repeat)
        with open(filename, 'w') as file:
            json.dump(data, file)
            
            
if __name__ == "__main__":
    args = load_args()
    
    model_name, job_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, job_dist, args['jobs'], server_dist, args['servers'])
    
    resource_ratio_testing(loaded_model_dist, args['repeat'])
