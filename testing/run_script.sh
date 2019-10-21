#!/bin/bash

#PBS -l nodes=1:ppn=4

#Change to the directory that the job was submitted from
cd ~/cloud_allocation/

# Load python 3.7
module load conda/4.4.0
source activate env37

# Load cplex
module load cplex/12.7.1

# Load Gurobi
module load gurobi/8.1.1
export GRB_LICENSE_FILE=/local/software/gurobi/8.1.1/gurobi.lic

# Run the python script
cmd="python -m testing.tests.$file $model $num_jobs $num_servers $repeat"
echo "Running $cmd"
eval "$cmd"
