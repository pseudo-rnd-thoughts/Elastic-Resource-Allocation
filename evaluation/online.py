"""
All of the other evaluation scripts test the algorithm within a static / one-shot case, this script tests the greedy
    algorithms using batched time steps compared to an optimal fixed speed online case
"""

from __future__ import annotations

from typing import Iterable

from src.extra.model import ModelDistribution


def batch_online(model_dist: ModelDistribution, repeat_num: int, repeats: int = 10,
                 batch_lengths: Iterable[int] = (1, 5, 10, 15),
                 task_arrival_rate_mean: int = 1, task_arrival_rate_std: int = 0.4):
    pass
