import subprocess, os
os.chdir('/kaggle/working')
B = 'https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./main/tools/lt7/'
for f in ['job8.py', 'runner7.py', 'post8.py', 'push8.py', 'tts8.py', 'tts_stage8.py']:
    subprocess.run('curl -sSL -o %s %s%s' % (f, B, f), shell=True)
exec(open('job8.py').read())
