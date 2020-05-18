#Upload a list of video files to pylon5 and check if files already exist (pseudo-code example)
#Imports for sftp:
import pysftp

#Define videos to send to server
newfns= list_of_local_video_file_paths #gathered in whatever way you see fit

#Initialize connection to PSC pylon5:
remote_loc='/pylon5/grant_id/userid/videos' #This is your intended destination on pylon5
srvr=pysftp.Connection('data.bridges.psc.edu',username='userid',password='yourpassword',port=22)
srvr.cwd(remote_loc)
for i,d in enumerate(newfns):
    if srvr.exists(newfns[i]):
        print('%d) %s found, skipping.' % (i,newfns[i]))
    else:
        print('%d) moving %s....' % (i,newfns[i]))
        srvr.put(d,newfns[i])
        print('     Finished.')
print('Finished all! Files moved!')
f=srvr.listdir()
#for i in f:
#    print(i)
srvr.close()
