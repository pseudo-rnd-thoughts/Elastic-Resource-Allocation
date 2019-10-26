"""Task events analysis"""

from datetime import datetime
from memory_profiler import profile

import pandas as pd

@profile
def analysis():
    """
    Analysis the task events file
    """
    print("Start loading csv at {}".format(datetime.now()))
    df: pd.DataFrame = pd.read_csv('complete_task_events.csv', header=None,
                                   names=['timestamp', 'missing info', 'job ID', 'task index within the job',
                                          'machine ID', 'event type', 'user name', 'scheduling class', 'priority',
                                          'resource request for CPU cores', 'resource request for RAM',
                                          'resource request for local disk space', 'different-machine constraint'])
    print("Finished at {}".format(datetime.now()))

    print("\nOriginal df: {}\n{}".format(df.shape, df.head(6)))

    df = df[['timestamp', 'job ID', 'task index within the job', 'machine ID', 'event type', 'scheduling class',
             'priority', 'resource request for CPU cores', 'resource request for RAM',
             'resource request for local disk space']]
    print("\nImportant info df: {}\n".format(df.shape))

    df = df[(df['resource request for CPU cores'].notnull()) &
            (df['resource request for RAM'].notnull()) &
            (df['resource request for local disk space'].notnull()) &
            (df['resource request for CPU cores'] > 0) &
            (df['resource request for RAM'] > 0) &
            (df['resource request for local disk space'] > 0)]
    print("\nValid requests df: {}\n".format(df.shape))

    print("\nAdding task ID\n")
    df['task ID'] = df['job ID'].map(str) + df['task index within the job'].map(str)
    df['task ID'] = df['task ID'].map(int)

    task_ids = df['task ID'].unique()
    print("Number of task ids: {}".format(task_ids.shape))

    print("Finding all finished tasks")
    df.grouped('task ID')['event type'].apply(list)
    finished_task_ids = []
    for task_id in task_ids:
        task_id_events = df[df['task ID'] == task_id]['event type']
        # Kick out all tasks that didnt finish or were stopped part of the way through
        if 0 in task_id_events and 1 in task_id_events and 4 in task_id_events and \
                2 not in task_id_events and 3 not in task_id_events and 5 not in task_id_events:
            finished_task_ids.append(task_id)
    print("Number of finished task is {}".format(len(finished_task_ids)))

    df = df[df['task ID'].isin(finished_task_ids)]
    print("\nFinish tasks: {}\n{}".format(df.shape, df.head(6)))

    timestamped_jobs_df = pd.DataFrame(columns=['job ID', 'task index within the job', 'task ID',
                                                'machine ID', 'event type', 'user name', 'scheduling class', 'priority',
                                                'resource request for CPU cores', 'resource request for RAM',
                                                'resource request for local disk space', 'different-machine constraint',
                                                'submit time', 'scheduled time', 'finish time', 'task schedule time',
                                                'task execution time'])
    for finished_task_id in finished_task_ids:
        task_id_info = df[df['task ID'] == finished_task_id]
        sorted_timestamps = task_id_info.sort_values('timestamp')
        data = sorted_timestamps.iloc[0:3, :]

        submit_time = data.iloc[0, 0]
        scheduled_time = data.iloc[1, 0]
        finish_time = data.iloc[2, 0]
        task_schedule_time = scheduled_time - submit_time
        task_execution_time = finish_time - scheduled_time

        job_id = data.iloc[0, 2]
        task_index_within_job = data.iloc[0, 3]
        machine_id = data.iloc[0, 4]
        event_type = data.iloc[0, 5]
        user_name = data.iloc[0, 6]
        scheduling_class = data.iloc[0, 7]
        priority = data.iloc[0, 8]
        cpu = data.iloc[0, 9]
        ram = data.iloc[0, 10]
        local_disk_space = data.iloc[0, 11]
        different_machine_constraint = data.iloc[0, 12]

        timestamped_jobs_df.append({'job ID': job_id, 'task index within the job': task_index_within_job,
                                    'task ID': finished_task_id, 'machine ID': machine_id, 'event type': event_type,
                                    'user name': user_name, 'scheduling class': scheduling_class, 'priority': priority,
                                    'resource request for CPU cores': cpu, 'resource request for RAM': ram,
                                    'resource request for local disk space': local_disk_space,
                                    'different-machine constraint': different_machine_constraint,
                                    'submit time': submit_time, 'scheduled time': scheduled_time,
                                    'finish time': finish_time, 'task schedule time': task_schedule_time,
                                    'task execution time': task_execution_time}, ignore_index=True)

    print("Start saving timestamped csv at {}".format(datetime.now()))
    timestamped_jobs_df.to_csv('timestamped_task_events.csv', index=False)
    print("Finished at {}".format(datetime.now()))


if __name__ == "__main__":
    analysis()
