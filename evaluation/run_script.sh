#!/bin/bash

#PBS -l walltime=60:00:00
#PBS -l nodes=1:ppn=8

#Change to the directory that the job was submitted from
cd ~/Flexible-Cloud-Resource/

# Load python 3.7
module load conda/4.4.0
source activate env37

# Load cplex
module load cplex/12.7.1

# Run the python script
echo $PWD
PYTHONPATH=~/Flexible-Cloud-Resource/src/
cmd="python -m evaluation.$file -f='$model_file' -t='$num_tasks' -s='$num_servers' -r='$repeat' -e='$extra'"
echo "Running $cmd"
eval "$cmd"
