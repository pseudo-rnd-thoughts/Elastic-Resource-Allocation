#!/bin/bash

for i in [@]; do
  eval "qsub -v \$file=$1 test.sh"
then
