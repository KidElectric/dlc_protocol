# DeepLabCut v. 2.1.7 protocol for use on Cluster / Supercomputer / Server using docker -> singularity image
BI - 2020-05-18

This repository contains example Python, SLURM and shell scripts for getting deeplabcut v. 2.1.7 working on a GPU cluster / server using a singularity image. This example is written for the Bridges / PSC / XSEDE GPU-AI nodes but could be adapted to other cluster environments.

The deeplabcut docker is based of the original docker instructions found here: https://github.com/DeepLabCut/Docker4DeepLabCut2.0 but will use a docker image hosted on dockerhub that can be pulled onto the cluster and built into a singularity image instead. (So no need to re-create the docker unless you would like to update it / alter it).

Throughout the protocol `userid` will be your Cluster / Server / PSC user ID for example, mine is ‘bisett.’ And `$SCRATCH` represents the directory on the server where your data and model are stored.

Many steps assume you are logged into the cluster via ssh, for example using:

`ssh -l userid bridges.psc.xsede.org`

1. Using SFTP to import videos onto pylon5 / cluster storage space (skip if videos are already on server or if unnecessary)

	1. It’s possible to login to bridges OnDemand and drag/drop files in the file explorer:
		https://ondemand.bridges.psc.edu/pun/sys/dashboard

	1. On a LINUX machine or using Ubuntu App in Windows / putty, manually add files by sftp:	
		`sftp -P 2222 userid@data.bridges.psc.edu` 

	1. To use python for more automated uploading process:
		1.	Connect to sftp or ssh to PSC at least once to generate SSH keys
		1.	On local computer run `pip install pysftp` to install python sftp package
		1.	See: pysftp_example.py for simple call
		1.	See: pysftp_upload.py for full upload pseudo-code example
		
1. Import DLC docker from dockerhub and make a singularity image

	1. Log into PSC using ssh (described above)
	
	1. Load singularity: module load singularity
	
	1. Move to desired directory for singularity image, for example: cd $SCRATCH
	
	1. Import a working DLC docker and create singularity image:
	
		`singularity build dlc_217.simg docker://kidelectric/deeplabcut:ver_2_1_7`
		
	1. Your current directory should have a file called dlc_217.simg when this is done.
	
	1. You should be able to run a shell in this image, for example:
	
		`singularity shell dlc_217.simg`
	1. Note: deeplabcut is available as a module in python3 in this image
		
	1. Note: It is possible to make your own docker and push that to dockerhub if you wish to make changes. See docker documentation for details on docker push. https://ropenscilabs.github.io/r-docker-tutorial/04-Dockerhub.html
	
1. Upload your trained model to PSC (or if training done on server, skip this step)

	1. Copy the DLC trained model project folder onto $SCRATCH 
	
	1. Copy the pre-trained resnet_v1_50.ckpt model to a location in $SCRATCH (only need to do this first time)
	
	1. Edit the project .yaml files to reference these server locations! In particular: project’s main config.yaml and /train/pose_cfg.yaml and /test/pose_cfg.yaml (if required). This can be done using the onDemand file editor in PSC if using Bridges, or vim via ssh.
	
	1. Note: Absolute paths seem to work better than relative paths, i.e. /pylon5/grantid/userid/project as opposed to ./project
	
1. Prepare 3 scripts necessary for running jobs in parallel on PSC:
	1. Job script, look at `sing_batch.job` for more details, but essentially:
		1. This file is a SLURM .job script that loads singularity module and executes linux script using the converted docker image: `singularity exec --nv dlc_217.simg ./sing.sh $SLURM_ARRAY_TASK_ID` -- --nv enables CUDA support, and $SLURM_ARRAY_TASK_ID is the number assigned during the sbatch job array call which can be passed all the way into Python to pick which videos to analyze. Each video can be analyzed in parallel using this method (for as many GPU nodes are available)
		1. Make sure .job file is executable: `chmod +x sing_batch.job`			
		1. If you wrote it in windows, make sure to fix new line characters: `sed -i -e 's/\r$//' sing_batch.job`

	1. A linux .sh script to call within the singularity image, See: `sing.sh`, essentially:
		
		```
		export DLClight=True #headless DLC mode
		python3 dlc_jobarray.py $1 #Passes slurm array task id to python script
		```
	1. The python script-- loads deeplabcut and perform analysis, See: `dlc_jobarray.py`, essentially:
		
		```
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
		```

1. Finally, write the sbatch command as a job array to recruit GPU nodes as quickly as they become available:
	1. ssh into the server as described above.
	1. cd to directory with sing_batch.job, e.g. `cd $SCRATCH`
	1. For example, to process the first 10 videos on volta16 GPUs in parallel type: `sbatch -p GPU-AI -N 1 --gres=gpu:volta16:1 -t 03:00:00 --array=0-9 sing_batch.job`
	1. The numbers after --array are the number of jobs that will each get assigned to a GPU node. This task ID will also be passed as the local env variable $SLURM_ARRAY_TASK_ID -- This makes it easy to resume at a certain video etc by passing a different array range. See SLURM job array documentation for more details (https://slurm.schedmd.com/job_array.html)
	1. If you know the absolute longest amount of time it could take to analyze one of your videos, update the max time HH:MM:SS after the -t option to reflect that time. the -t command requests a certain max amount of time, and shorter times may be available more quickly on a given cluster.
	1. Check the slurm_.out files to see what did and didn't work!
	1. .csv analysis files will be saved to the project/videos directory
	1. It’s possible to debug this code in an interactive session: requested via: `interact -p GPU-AI --gres=gpu:volta16:1 -t 01:00:00 --egress`

