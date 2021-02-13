"""
Model distributed generated from Alibaba cluster dataset
"""

from typing import Optional, List
import random as rnd

from src.core.server import Server
from src.core.task import Task
from src.extra.model import ModelDistribution
import pandas as pd


class AlibabaModelDistribution(ModelDistribution):
    """Alibaba Model Distribution"""

    def __init__(self, filename: str, num_tasks: Optional[int] = None, num_servers: Optional[int] = None):
        super().__init__(filename, num_tasks, num_servers)

        self.task_model = pd.read_csv(self.model_data['task_filename'])

    def generate_tasks(self, servers: List[Server]) -> List[Task]:
        return [self.generate_rnd_task(task_id, servers) for task_id in range(self.num_tasks)]

    def generate_servers(self) -> List[Server]:
        pass

    def generate_rnd_task(self, task_id: int, servers: List[Server]) -> Task:
        task_row = self.task_model.sample()

        return Task(f'realistic {task_id}',
                    required_storage=task_row['mem_max'],
                    required_computation=task_row['total_cpu'],
                    required_results_data=rnd.randint(20, 60) * task_row['plan_mem'],
                    value=None, deadline=task_row['time_taken'])
