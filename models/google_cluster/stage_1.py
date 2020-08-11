"""Stage 1"""

import pandas as pd

# Reads the complete full data files
df = pd.read_csv('combined_data.csv', header=None, names=['timestamp', 'missing info', 'job ID', 'task index within the job', 'machine ID', 'event type', 'user name', 'scheduling class', 'priority', 'cpu', 'ram', 'disk', 'different-machine constraint'])

# Reduce the df to the required columns
df = df[['timestamp', 'job ID', 'task index within the job', 'event type', 'priority', 'cpu', 'ram', 'disk']]
print(df)
print()
# Add the task id
df['task ID'] = df['job ID'].map(str) + df['task index within the job'].map(str)
df['task ID'] = df['task ID'].map(int)

# Update the df
df = df[['task ID', 'timestamp', 'event type', 'priority', 'cpu', 'ram', 'disk']]
print(df)
print()

# Get the successful and unusable tasks
successful_tasks = df[df['event type'] == 4]['task ID']
print(successful_tasks)
print()

unusable_tasks = df[df['event type'].isin([2, 3, 5, 6, 7, 8]) | (df['timestamp'] == 0)]['task ID']
print(unusable_tasks)
print()

# Limit the tasks to just the IDs in the successful jobs and not unusable task
usable_df = df[(df['task ID'].isin(successful_tasks)) & (~df['task ID'].isin(unusable_tasks)) & (df['event type'] != 0)]
print(usable_df)
usable_df.to_csv('unusable_tasks.csv', index=False)

"""

schedule_df = df[['timestamp', 'event type', 'task ID']][df['event type'] == 1].rename(columns={'timestamp': 'schedule time'}).set_index('task ID')
finish_df = df[['timestamp', 'event type', 'task ID']][df['event type'] == 4].rename(columns={'timestamp': 'finish time'}).set_index('task ID')

df = df[['timestamp', 'task ID', 'priority', 'cpu', 'ram', 'disk']]
compute_df = finish_df['finish time'].map(int) - schedule_df['schedule time'].map(int)


# Group the df by the resources and get the count
resource_df = df.groupby(['priority', 'cpu', 'ram', 'disk']).size().reset_index().rename(columns={0: 'count'})

# Save the resource df
resource_df.to_csv('job_resource.csv', index=False)

# Find all of the jobs that are popular
cols = ['priority', 'cpu', 'ram', 'disk']

top_resource_df = resource_df[resource_df['count'] > 1000]
"""