#!/bin/bash
export DLClight=True
echo "JOB ID IN SINGULARITY SCRIPT:"
echo $1
python3 dlc_jobarray.py $1