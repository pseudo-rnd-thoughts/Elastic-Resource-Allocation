#!/usr/bin/env bash

read -p 'Script: ' script
read -p 'Model: ' model
read -p 'Num of repeats: ' repeats

jobs=()
servers=()
while true; do
  read -p 'Num of jobs: ' num_jobs
  if [ "$num_jobs" == "" ]; then
    break
  else
    read -p 'Num of servers: ' num_servers
  fi
  jobs+=("$num_jobs")
  servers+=("$num_servers")
done

for (( pos = 0; pos < ${#jobs[@]}; pos++ )); do
  for (( repeat = 0; repeat < repeats; repeat++ )); do
    cmd="qsub -v file='$script'_testing,num_jobs='${jobs[pos]}',num_servers='${servers[pos]}',model='$model',repeat='$repeat' run_script.sh"
    eval "$cmd"
  done
done
