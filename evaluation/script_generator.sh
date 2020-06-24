#!/usr/bin/env bash

read -p 'Script: ' script
read -p 'Model: ' model_file
read -p 'Num of repeats: ' repeats

tasks=()
servers=()
while true; do
  read -p 'Num of tasks: ' num_task

  if [ "$num_task" == "" ]; then
    echo 'No more tasks and servers'
    break
  else
    read -p 'Num of servers: ' num_servers
  fi

  tasks+=("$num_tasks")
  servers+=("$num_servers")
done

read -p 'Extra info: ' extra

for (( pos = 0; pos < ${#jobs[@]}; pos++ )); do
  for (( repeat = 0; repeat < repeats; repeat++ )); do
    cmd="qsub -v file='$script',model_file='$model_file',num_task='${tasks[pos]}',num_servers='${servers[pos]}',repeat='$repeat',extra='$extra' run_script.sh"
    echo "$cmd"
    eval "$cmd"
  done
done
