"""
Test the model distribution files
"""

import os

from extra.model import ModelDistribution


def test_model_distribution():
    files = os.listdir('models/')
    for file in files:
        model_dist = ModelDistribution(f'models/{file}', 2, 2)

        tasks, servers = model_dist.generate()
