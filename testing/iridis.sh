#!/bin/bash
# Example Bash Script to execute <executable_name> on batch

#Change to the directory that the job was submitted from
cd $PBS_O_WORKDIR
echo pwd
#Run <executable_name> from the working directory
./iridis.sh