#!/usr/bin/env bash

args=$@
script=${args[0]}

if [ ${#args[@]} == 1 ]; then
  args=("" 12 2 15 3 25 5)
elif [ "$2" == "big" ]; then
  args=("" 12 2 15 3 25 5 100 20 150 25)
fi

for (( pos = 1; pos < ${#args[@]}; pos+=2 )); do
    cmd="qsub -v file='$script',num_jobs='${args[pos]}',num_servers='${args[pos+1]}' run_file.sh"
    eval "$cmd"
done
