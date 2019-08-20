#!/bin/bash
# Example Bash Script to execute <executable_name> on batch

#PBS –l walltime=16:00:00
#PBS –l nodes=1:ppn=16
#PBS -m ae -M mt5g17@soton.ac.uk

#Change to the directory that the job was submitted from
cd /lyceum/mt5g17/cloud_allocation/testing

#Run <executable_name> from the working directory
./run_iridis.sh