#!/usr/bin/env bash

read -p 'Script: ' script
read -p 'Model: ' model_file
read -p 'Num of repeats: ' repeats

tasks=()
servers=()
while true; do
  read -p 'Num of tasks: ' num_tasks
  if [ "$num_tasks" == "" ]; then
    printf "\nTasks: ${tasks[*]}\nServer: ${servers[*]} \n"
    break
  else
    read -p 'Num of servers: ' num_servers
  fi

  tasks+=("$num_tasks")
  servers+=("$num_servers")
done

read -p 'Extra info: ' extra

for (( pos = 0; pos < ${#tasks[@]}; pos++ )); do
  for (( repeat = 0; repeat < repeats; repeat++ )); do
    cmd="qsub run_script.sh -v file='$script',model_file='$model_file',num_tasks='${tasks[pos]}',num_servers='${servers[pos]}',repeat='$repeat',extra='$extra' run_script.sh"
    printf "Command: $cmd \n"
    eval "$cmd"
  done
done
