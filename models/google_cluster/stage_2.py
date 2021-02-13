"""Stage 2"""

import pandas as pd

# timestamp, job ID, task index within the job, event type, scheduling class, priority, resource request for CPU cores,
#   resource request for RAM, resource request for local disk space, task ID
df = pd.read_csv('unusable_tasks.csv')

schedule_df = df[['timestamp', 'event type', 'task ID']][df['event type'] == 1]\
    .rename(columns={'timestamp': 'schedule time'})
finish_df = df[['timestamp', 'event type', 'task ID']][df['event type'] == 4]\
    .rename(columns={'timestamp': 'finish time'})

time_df = pd.merge(schedule_df, finish_df, on='task ID')
time_df = time_df[['task ID', 'schedule time', 'finish time']]

time_df['compute time'] = round((time_df['finish time'] - time_df['schedule time']) / (10 ** 6), 2)
time_df['finish time'] = round(time_df['finish time'] / (10 ** 6), 2)
time_df['schedule time'] = round(time_df['schedule time'] / (10 ** 6), 2)

task_df = df[['task ID', 'priority', 'cpu', 'ram', 'disk']].drop_duplicates()
task_time_df = pd.merge(task_df, time_df, on='task ID')

task_time_df.to_csv('task_time.csv', index=False)
