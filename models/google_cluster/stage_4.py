"""
Stage 4 for the calculating tasks from google cloud dataset
"""

import pandas as pd
import json

df = pd.read_csv('google_model.csv')

model = []

print(df['probability'].sum())

df = df[df['probability'] > 0.0001]
print(df)
for index, (cpu, ram, disk, probability, mean_time, std_time) in df.iterrows():
    model.append({
        "name": str(index),
        "probability": round(probability, 4),
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

print(df['probability'].sum())

with open('google_model.json', 'w') as file:
    json.dump(model, file)
print("Finished")
