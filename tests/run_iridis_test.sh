#!/bin/bash

#PBS -l walltime=48:00:00
#PBS -l nodes=1:ppn=8

#Change to the directory that the job was submitted from
cd ~/Flexible-Cloud-Resource/

# Load python 3.7
module load conda/4.4.0
source activate env37

# Load cplex
module load cplex/12.7.1

# Run the python script
cmd="PYTHONPATH=~/Flexible-Cloud-Resource/src/ python tests/test_iridis"
echo "Running $cmd"
eval "$cmd"
