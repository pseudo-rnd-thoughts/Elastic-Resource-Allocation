#!/bin/bash

#PBS -l walltime=16:00:00
#PBS -l nodes=1:ppn=16
#PBS -m ae -M mt5g17@soton.ac.uk

#Change to the directory that the job was submitted from
cd ~/cloud_allocation/

module load conda/4.4.0
source activate env37

module load cplex/12.7.1

cmd='python -m testing.iridis.$1'
eval $cmd