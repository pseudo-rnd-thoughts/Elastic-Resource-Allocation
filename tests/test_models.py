"""
Test the model distribution files
"""

import json
import os
import random as rnd
import sys

from extra.io import parse_args
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


def test_args():
    print()

    # Files
    sys.argv = ['location', '--file', 'basic']
    assert parse_args() == {'model': 'models/basic.mdl', 'tasks': None, 'servers': None, 'repeat': 0}
    sys.argv = ['location', '-f', 'test']
    assert parse_args() == {'model': 'models/test.mdl', 'tasks': None, 'servers': None, 'repeat': 0}

    sys.argv = ['location', '--file', 'basic', '--tasks', '3']
    assert parse_args() == {'model': 'models/basic.mdl', 'tasks': 3, 'servers': None, 'repeat': 0}
    sys.argv = ['location', '--file', 'basic', '-t', '4']
    assert parse_args() == {'model': 'models/basic.mdl', 'tasks': 4, 'servers': None, 'repeat': 0}

    sys.argv = ['location', '--file', 'basic', '--servers', '5']
    assert parse_args() == {'model': 'models/basic.mdl', 'tasks': None, 'servers': 5, 'repeat': 0}
    sys.argv = ['location', '--file', 'basic', '-s', '6']
    assert parse_args() == {'model': 'models/basic.mdl', 'tasks': None, 'servers': 6, 'repeat': 0}

    sys.argv = ['location', '--file', 'basic', '--repeat', '7']
    assert parse_args() == {'model': 'models/basic.mdl', 'tasks': None, 'servers': None, 'repeat': 7}
    sys.argv = ['location', '--file', 'basic', '-r', '8']
    assert parse_args() == {'model': 'models/basic.mdl', 'tasks': None, 'servers': None, 'repeat': 8}

    sys.argv = ['location', '--file', 'basic', '--tasks', '1', '--servers', '2', '--repeat', '3']
    assert parse_args() == {'model': 'models/basic.mdl', 'tasks': 1, 'servers': 2, 'repeat': 3}
    sys.argv = ['location', '--file', 'basic', '-t', '1', '-s', '2', '-r', '3']
    assert parse_args() == {'model': 'models/basic.mdl', 'tasks': 1, 'servers': 2, 'repeat': 3}
