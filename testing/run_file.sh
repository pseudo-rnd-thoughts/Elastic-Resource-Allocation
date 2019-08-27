#!/bin/bash

#PBS -l walltime=24:00:00
#PBS -l nodes=1:ppn=8

#Change to the directory that the job was submitted from
cd ~/cloud_allocation/

module load conda/4.4.0
source activate env37

module load cplex/12.7.1

cmd="python -m testing.tests.$file $num_jobs $num_servers"
eval $cmd

# Example script: qsub -v file="optimality_test" run_file.sh