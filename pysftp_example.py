import pysftp
srvr=pysftp.Connection('data.bridges.psc.edu',username='userid',password='yourpassword',port=22)
srvr.cwd('/$HOME')
dirs=srvr.listdir()
for d in dirs:
    print(d) #Print everything in your home directory
