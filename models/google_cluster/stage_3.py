"""Stage 3"""

import pandas as pd
import numpy as np
import json

# Resource count
# priority, cpu, ram, disk, count
resource_df = pd.read_csv('resource_count.csv')

resource_df['count'] = resource_df['count'] // 3
resource_df = resource_df[(resource_df['cpu'] > 0) & (resource_df['ram'] > 0) & (resource_df['disk'] > 0)]

top_resource_df = resource_df[resource_df['count'] >= 1000]

# The task time
# task ID, priority, cpu, ram, disk, finish time, schedule time, compute time
task_time_df = pd.read_csv('task_time.csv')
task_time_df['compute time'] = task_time_df['compute time'].map(int)
task_time_df = task_time_df[(task_time_df['cpu'] > 0) & (task_time_df['ram'] > 0) & (task_time_df['disk'] > 0)]

times_df = task_time_df[['priority', 'cpu', 'ram', 'disk', 'compute time']].groupby(by=['priority', 'cpu', 'ram', 'disk']).agg(lambda x: list(x))

resource_time_df = pd.merge(top_resource_df, times_df, on=['priority', 'cpu', 'ram', 'disk'])
print(resource_time_df)

resource_time_df['cpu'] = round(resource_time_df['cpu'] / resource_time_df['cpu'].min(), 0)
resource_time_df['ram'] = round(resource_time_df['ram'] / resource_time_df['ram'].min(), 0)
resource_time_df['disk'] = round(resource_time_df['disk'] / resource_time_df['disk'].min(), 0)

resource_time_df['cpu'] = resource_time_df['cpu'].map(int)
resource_time_df['ram'] = resource_time_df['ram'].map(int)
resource_time_df['disk'] = resource_time_df['disk'].map(int)
print(resource_time_df)

resource_time_df['mean time'] = resource_time_df['compute time'].apply(lambda x: np.mean(x))
resource_time_df['std time'] = resource_time_df['compute time'].apply(lambda x: np.std(x))
print(resource_time_df)

resource_time_df = resource_time_df[resource_time_df['mean time'] > resource_time_df['std time'] * 4]
print(resource_time_df)

total = resource_time_df['count'].sum()
resource_time_df['probability'] = resource_time_df['count'] / total

resource_time_df['mean time'] = resource_time_df['mean time'].map(int)
resource_time_df['std time'] = resource_time_df['std time'].map(int)

print(resource_time_df)
resource_time_df = resource_time_df[['cpu', 'ram', 'disk', 'probability', 'mean time', 'std time']]
model = []
for index, (cpu, ram, disk, probability, mean_time, std_time) in resource_time_df.iterrows():
    model.append({
        "name": str(index),
        "probability": round(probability, 5),
        "required_storage_mean": disk,
        "required_storage_std": 0,
        "required_computation_mean": cpu,
        "required_computation_std": 0,
        "required_results_data_mean": ram,
        "required_results_data_std": 0,
        "value_mean": disk * cpu * ram,
        "value_std": 0,
        "deadline_mean": mean_time
    })

with open('google_model.json', 'w') as file:
    json.dump(model, file)
