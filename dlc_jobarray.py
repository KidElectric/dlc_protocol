import sys
import deeplabcut
from os import listdir
jobid=int(sys.argv[1])
print("Job ID IN PYTHON: %d" % jobid)

project_path='./projects/psc_analyze-BRI-2020-05-01/'
path_config_file = project_path + 'config_10.yaml'
video_path= project_path + 'videos/'
vids=[v for v in listdir(video_path) if '.mpg' in v]
video=vids[jobid]
print("Analyzing video %d / %d: %s" % (jobid,len(vids),video))
deeplabcut.analyze_videos(path_config_file,[video_path + video],gputouse=0,batchsize=8,save_as_csv = True)
print("Succeeded")