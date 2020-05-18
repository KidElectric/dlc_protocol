# DeepLabCut v. 2.1.7 protocol for use on Cluster / Supercomputer / Server using docker -> singularity image
BI - 2020-05-18

This repository contains example Python, SLURM and shell scripts for getting deeplabcut v. 2.1.7 working on a GPU cluster / server using a singularity image. This example is written for the Bridges / PSC / XSEDE GPU-AI nodes but could be adapted to other cluster environments.

The deeplabcut docker is based of the original docker instructions found here: https://github.com/DeepLabCut/Docker4DeepLabCut2.0 but will use a docker image hosted on dockerhub that can be pulled onto the cluster and built into a singularity image instead. (So no need to re-create the docker unless you would like to update it / alter it).

Throughout the protocol 'userid' will be your Cluster / Bridges / PSC user ID for example, mine is ‘bisett.’

Many steps assume you are logged into the cluster via ssh, for example using:
ssh -l userid bridges.psc.xsede.org

1) Using SFTP to import videos onto pylon5 / cluster storage space (skip if videos are already on server or if unnecessary)
	a. It’s possible to login to bridges OnDemand and drag/drop files in the file explorer:
		https://ondemand.bridges.psc.edu/pun/sys/dashboard

	b. On a LINUX machine or using Ubuntu App in Windows / putty:
		sftp -P 2222 userid@data.bridges.psc.edu
		(and use sftp manually If applicable).

	c.	To use python for more automated uploading process:
		i.	Connect to sftp or ssh to PSC at least once to generate SSH keys
		ii.	On local computer run ‘pip install pysftp’ to install python sftp package
		iii.	See: pysftp_example.py for simple call
		iv.	See: pysftp_upload.py for full upload pseudo-code example
		
2) Import DLC docker from dockerhub and make a singularity image
	a. Log into PSC using ssh (described above)
	b. Load singularity: module load singularity
	c. Move to desired directory for singularity image, for example: cd $SCRATCH
	d. Import a working DLC docker and create singularity image:
		singularity build dlc_217.simg docker://kidelectric/deeplabcut:ver_2_1_7
	e. Your current directory should have a file called dlc_217.simg when this is done.
	f. You should be able to run a shell in this image, for example:
		singularity shell dlc_217.simg 
	g. Note: It is possible to make your own docker and push that to dockerhub if you wish to make changes or make your 		own docker. See docker documentation for details on docker push.
3) Upload a trained model to PSC
	a. Copy the DLC trained model project folder onto $SCRATCH 
	b. Copy the pre-trained resnet_v1_50.ckpt model to a location in $SCRATCH
	c. Edit the project .yaml files to reference these server locations! In particular: project’s main config.yaml and /train/pose_cfg.yaml and /test/pose_cfg.yaml (if required)
	d. Note: Absolute paths seem to work better than relative paths, i.e. /pylon5/grantid/userid/ as opposed to $SCRATCH
4) Prepare 3 scripts necessary for running jobs in parallel on PSC:

	a. Job script
		i. See: sing_batch.job, essentially:
		#!/bin/bash
		set -x
		source /etc/profile.d/modules.sh
		module load singularity
		cd $SCRATCH
		singularity exec --nv dlc_217.simg ./sing.sh $SLURM_ARRAY_TASK_ID
		ii. Note: $SLURM_ARRAY_TASK_ID is a number assigned during the batch call which can be passed all the way into Python to pick which videos to analyze. Each video can be analyzed in parallel using this method (for as many GPU nodes are available)
		iii. Make sure .job file is executable: chmod +x sing_batch.job
		iv. If you wrote it in windows, make sure to fix new line characters:
			sed -i -e 's/\r$//' sing_batch.job

	b. A linux .sh script to call within the singularity image:
		i. See: sing.sh, essentially:
		export DLClight=True #headless DLC mode
		python3 dlc_jobarray.py $1 #Passes slurm array task id to python script

	c. A python script to load deeplabcut and perform analysis
		i. See: dlc_jobarray.py, essentially:
		import sys
		import deeplabcut
		jobid=int(sys.argv[1])
		print("Job ID in PYTHON: %d" % jobid)
		project_path='./projects/dlc_analyze/'
		path_config_file = project_path + 'config.yaml'
		video_path= project_path + 'videos/'
		vids=[v for v in listdir(video_path) if '.mpg' in v]
		video=vids[jobid]
		print("Analyzing video %d / %d: %s" % (jobid,len(vids),video))
		deeplabcut.analyze_videos(path_config_file,[video_path + video],gputouse=0,batchsize=8,save_as_csv = True)
		print("Succeeded")

5) Create an array sbatch command:
	a. Ssh into the server as described above.
	b. cd to directory with sing_batch.job
	c. For example, to process the first 10 videos on volta16 GPUs in parallel type:
	d. sbatch -p GPU-AI -N 1 --gres=gpu:volta16:1 -t 03:00:00 --array=0-9 sing_batch.job
	e. The numbers after --array are the local variable $SLURM_ARRAY_TASK_ID assigned to each new instance opened on a GPU node. This makes it easy to resume at a certain video etc. 
	f. If you know the absolute longest it could take to analyze a video, update the max time HH:MM:SS after the -t option to be that time.
	g. It’s possible to debug this code in an interactive session: requested via:
	h. interact -p GPU-AI --gres=gpu:volta16:1 -t 01:00:00 --egress
