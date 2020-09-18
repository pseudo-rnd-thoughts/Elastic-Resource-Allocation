"""
Stage 5 for the calculating tasks from google cloud dataset
"""
import pandas as pd
import json

df = pd.read_csv('machine_events.csv', header=None,
                 names=['timestamp', 'machine ID', 'event type', 'platform ID', 'cpu', 'memory'])

print(df)

df = df[df['event type'] == 0]
df = df[['cpu', 'memory']]

df['cpu'] = round(df['cpu'] / 0.0006247, 0)
df['memory'] = round(df['memory'] / 0.0001554, 0)

print(df)

df = df.groupby(by=['cpu', 'memory']).size().reset_index().rename(columns={0: 'count'})
print(df)

df = df[df['count'] > 100]
print(df)

df['probability'] = round(df['count'] / df['count'].sum(), 4)

model = []
for index, (cpu, memory, count, prob) in df.iterrows():
    model.append({
      "name": str(index),
      "probability": prob,
      "maximum_storage_mean": memory,
      "maximum_storage_std": 0,
      "maximum_computation_mean": cpu,
      "maximum_computation_std": 0,
      "maximum_bandwidth_mean": memory * 1.5,
      "maximum_bandwidth_std": 0
    })

with open('google.model', 'w') as file:
    json.dump(model, file)
