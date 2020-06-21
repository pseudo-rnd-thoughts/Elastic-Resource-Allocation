"""
Test the model distribution files
"""

import json
import os
import random as rnd

from extra.model import ModelDistribution


def test_model_distribution():
    print()
    files = os.listdir('models/')
    for file in files:
        if file == "caroline.mdl":
            model_dist = ModelDistribution(f'models/caroline.mdl', num_tasks=2)

            tasks, servers = model_dist.generate()
            assert len(tasks) == 2
            assert len(servers) == 8
        else:
            model_dist = ModelDistribution(f'models/{file}', num_tasks=4, num_servers=3)

            tasks, servers = model_dist.generate()
            assert len(tasks) == 4
            assert len(servers) == 3


def test_model_probability():
    print()
    with open('models/basic.mdl') as file:
        file_data = json.load(file)

        task_probabilities = [task_distribution['probability'] for task_distribution in file_data['task distributions']]
        print(f'Task Probabilities: [{" ".join([str(prob) for prob in task_probabilities])}]')
        print(f'Sum probabilities: [{" ".join([str(sum(task_probabilities[:p+1])) for p in range(len(task_probabilities))])}]')

        prob = rnd.random()
        print(f'Probability: {prob}')
