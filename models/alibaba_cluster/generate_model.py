"""
Generates the alibaba model
"""

import os

import pandas as pd

batch_tasks_col_names = ['task_name', 'instance_num', 'job_name', 'task_type', 'status',
                         'start_time', 'end_time', 'plan_cpu', 'plan_mem']
batch_tasks: pd.DataFrame = pd.read_csv('batch_task.csv', names=batch_tasks_col_names)
print(batch_tasks)
batch_tasks = batch_tasks[(batch_tasks['instance_num'] == 1) & (batch_tasks['status'] == 'Terminated') &
                          (0 < batch_tasks['plan_cpu']) & (batch_tasks['plan_cpu'] < 600) &
                          (0 < batch_tasks['plan_mem']) & (batch_tasks['plan_mem'] < 4)]

batch_tasks = batch_tasks[['task_name', 'job_name', 'start_time', 'end_time', 'plan_cpu', 'plan_mem']]
print('Saving')
batch_tasks.to_csv('batch_task_reduced.csv', index=False)
print('Saved')

batch_tasks: pd.DataFrame = pd.read_csv('batch_task_reduced.csv')
print(batch_tasks)

chuck_size = 4000000
batch_instance_col_names = ['instance_name', 'task_name', 'job_name', 'task_type', 'status', 'start_time', 'end_time',
                            'machine_id', 'seq_no', 'total_seq_no', 'cpu_avg', 'cpu_max', 'mem_avg', 'mem_max']
with pd.read_csv('batch_instance.csv',
                 chunksize=chuck_size, names=batch_instance_col_names) as batch_instance_reader:
    for pos, batch_instance_chunk in enumerate(batch_instance_reader):
        print(pos)
        batch_task_instances = pd.merge(batch_tasks, batch_instance_chunk,
                                        on=['task_name', 'job_name', 'start_time', 'end_time'])
        # ['task_name', 'job_name', 'start_time', 'end_time', 'plan_cpu',
        #        'plan_mem', 'instance_name', 'task_type', 'status', 'machine_id',
        #        'seq_no', 'total_seq_no', 'cpu_avg', 'cpu_max', 'mem_avg', 'mem_max']
        batch_task_instances.to_csv(f'batch_task_instances/instance_{pos}.csv', index=False)

batch_task_instances = [pd.read_csv(f'batch_task_instances/{filename}')
                        for filename in os.listdir('batch_task_instances')]
batch_task_instances = pd.concat(batch_task_instances)
batch_task_instances['time_taken'] = batch_task_instances['end_time'] - batch_task_instances['start_time']
batch_task_instances = batch_task_instances[10 < batch_task_instances['time_taken']]
batch_task_instances = batch_task_instances[['task_name', 'job_name', 'time_taken', 'plan_cpu', 'plan_mem',
                                             'cpu_avg', 'cpu_max', 'mem_avg', 'mem_max']]

batch_task_instances.to_csv('batch_task_instances.csv', index=False)
