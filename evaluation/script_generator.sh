#!/usr/bin/env bash

read -p 'Script: ' script
read -p 'Model: ' model_file
read -p 'Num of repeats: ' repeats

tasks=()
servers=()
while true; do
  read -p 'Num of tasks: ' num_tasks
  read -p 'Num of servers: ' num_servers

  if [[ "$num_tasks" == '' && "$num_servers" == '' ]]; then
    printf "\nTasks: ${tasks[*]}\nServer: ${servers[*]} \n"
    break
  else
    if [ "$num_tasks" == '' ]; then
      $num_tasks=''
    fi
    if [ "$num_servers" == '' ]; then
      $num_servers=''
    fi

    tasks+=("$num_tasks")
    servers+=("$num_servers")
  fi
done

read -p 'Extra info: ' extra
if [ "$extra" == "" ]; then
  extra=' '
fi

for (( pos = 0; pos < ${#tasks[@]}; pos++ )); do
  for (( repeat = 0; repeat < repeats; repeat++ )); do
    cmd="qsub -v file='$script',model_file='$model_file',num_tasks='${tasks[pos]}',num_servers='${servers[pos]}',repeat='$repeat',extra='$extra' run_script.sh"
    printf "Command: $cmd \n"
    eval "$cmd"
  done
done
