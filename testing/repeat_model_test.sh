#!/usr/bin/env bash

args=($@)
script=${args[0]}

for (( repeat = 0; repeat < ${args[3]}; repeat+=1 )); do
    cmd="qsub -v file='$script',num_jobs='${args[1]}',num_servers='${args[2]}',repeat='$repeat' run_file.sh"
    echo "File: $script for ${args[1]} jobs and ${args[2]} servers"
    eval "$cmd"
done
