import subprocess, os
os.chdir('/kaggle/working')
subprocess.run('curl -sSL -o lsync_job.py https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./main/tools/ls1/lsync_job.py', shell=True)
exec(open('lsync_job.py').read())
