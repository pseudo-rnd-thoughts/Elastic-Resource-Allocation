#!/usr/bin/env bash

scripts=()
models=()
jobs=()
servers=()

while true; do
  read -p 'Script: ' script
  if [ "$script" == "" ]; then
    break
  else
    scripts+=("$script")
  fi
done

while true; do
  read -p 'Model: ' model
  if [ "$model" == "" ]; then
    break
  else
    models+=("$model")
  fi
done

read -p 'Num of repeats: ' repeats

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

for script in "${scripts[@]}"; do
  for model in "${models[@]}"; do
    for (( pos = 0; pos < ${#jobs[@]}; pos++ )); do
      for (( repeat = 0; repeat < repeats; repeat++ )); do
        cmd="qsub -v file='${script}_testing',num_jobs='${jobs[pos]}',num_servers='${servers[pos]}',model='$model',repeat='$repeat' run_script.sh"
        # eval "$cmd"
        echo "$cmd"
      done
    done
  done
done
