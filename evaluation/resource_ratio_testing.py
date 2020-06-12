import json

from tqdm import tqdm

from src.core.core import load_args, results_filename
from src.core.fixed_task import FixedTask, FixedSumSpeeds
from src.core.model import load_dist, ModelDist, reset_model
from src.greedy.greedy import greedy_algorithm
from src.greedy.resource_allocation_policy import SumPercentage, SumSpeed
from src.greedy.server_selection_policy import SumResources, TaskSumResources
from src.greedy.value_density import UtilityPerResources, UtilityResourcePerDeadline, UtilityDeadlinePerResource, Value
from src.optimal.fixed_optimal import fixed_optimal_algorithm
from src.optimal.optimal import optimal_algorithm


def resource_ratio_testing(model_dist: ModelDist, repeat: int, repeats: int = 10):
    data = []
    for _ in tqdm(range(repeats)):
        results = {}
        tasks, servers = model_dist.create()
        fixed_tasks = [FixedTask(task, FixedSumSpeeds()) for task in tasks]

        total_resources = {server: server.computation_capacity + server.bandwidth_capacity for server in servers}
        for ratio in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
            ratio_results = {}
            for server in servers:
                server.update_capacities(int(total_resources[server] * ratio),
                                         int(total_resources[server] * (1 - ratio)))

            optimal_results = optimal_algorithm(tasks, servers, 180)
            ratio_results['optimal'] = optimal_results.store(
                ratio=ratio, server_ratio={server: server.computation_capacity / server.bandwidth_capacity
                                           for server in servers}
            )

            reset_model(tasks, servers)

            fixed_results = fixed_optimal_algorithm(fixed_tasks, servers, 180)
            ratio_results['fixed'] = fixed_results.store(
                ratio=ratio, server_ratio={server: server.computation_capacity / server.bandwidth_capacity
                                           for server in servers}
            )

            reset_model(tasks, servers)

            greedy_policies = [
                (vd, ss, ra)
                for vd in [UtilityPerResources(), UtilityResourcePerDeadline(), UtilityDeadlinePerResource(), Value()]
                for ss in [SumResources(), SumResources(True),
                           TaskSumResources(SumPercentage()), TaskSumResources(SumPercentage(), True),
                           TaskSumResources(SumSpeed()), TaskSumResources(SumSpeed(), True)]
                for ra in [SumPercentage(), SumSpeed()]
            ]
            for (vd, ss, ra) in greedy_policies:
                try:
                    greedy_result = greedy_algorithm(tasks, servers, vd, ss, ra)
                    ratio_results[greedy_result.algorithm_name] = greedy_result.store()
                except Exception as e:
                    print(e)

                reset_model(tasks, servers)

            results['ratio {}'.format(ratio)] = ratio_results
        data.append(results)

        # Save the results to the file
        filename = results_filename('resource_ratio', model_dist.file_name, repeat)
        with open(filename, 'w') as file:
            json.dump(data, file)


if __name__ == "__main__":
    args = load_args()

    model_name, task_dist, server_dist = load_dist(args['model'])
    loaded_model_dist = ModelDist(model_name, task_dist, args['tasks'], server_dist, args['servers'])

    resource_ratio_testing(loaded_model_dist, args['repeat'])
