# After Seed-VC: clean every converted line, rebuild the master audio with Neko's voice, remux, then rebuild the avatar video.
import json, os, subprocess, sys, shutil
sys.path.insert(0,'/home/claude/svc'); import clean
M='/home/claude/ps91m'; AV='/home/claude/ps91av'; O='/home/claude/svc/outn'
os.makedirs(M+'/nv',exist_ok=True)
tl=json.load(open(M+'/tl.json')); miss=[]
for x in tl:
    if 'f' not in x: continue
    if not os.path.exists(f'{O}/{x["f"]}'): miss.append(x['f']); continue
    clean.run(f'{M}/{x["f"]}', f'{O}/{x["f"]}', f'{M}/nv/{x["f"]}', 24000)
assert not miss, miss
shutil.copy(M+'/tl.json', M+'/tl_kokoro.json')
tl2=[dict(x, f='nv/'+x['f']) if 'f' in x else x for x in tl]
json.dump(tl2, open(M+'/tl.json','w'), indent=1)
try:
    subprocess.check_call(['python3','asm_ps91.py','audio'], cwd=M)
finally:
    shutil.copy(M+'/tl_kokoro.json', M+'/tl.json')
subprocess.check_call(['ffmpeg','-y','-loglevel','error','-i',M+'/Psalm-91-Before-You-Walk-Out-the-Door.mp4','-i',M+'/mix.wav','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-shortest',M+'/master_nekovoice.mp4'])
for k in ['o1','o2','o3','o4','o5','c1','c2','c3','c4','c5','c6','c7']:
    src=f'/home/claude/svc/av/av_{k}.wav'; vc=f'{O}/av_{k}.wav'; cl=f'/home/claude/svc/av/clean_{k}.wav'
    clean.run(src, vc, cl, 24000)
    if not os.path.exists(f'{AV}/clip_{k}_flow.mp4'): shutil.copy(f'{AV}/clip_{k}.mp4', f'{AV}/clip_{k}_flow.mp4')
    subprocess.check_call(['ffmpeg','-y','-loglevel','error','-i',f'{AV}/clip_{k}_flow.mp4','-i',cl,'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000',f'{AV}/clip_{k}.mp4'])
env=dict(os.environ, MASTER=M+'/master_nekovoice.mp4')
subprocess.check_call(['python3','splice.py','all'], cwd=AV, env=env)
subprocess.check_call(['ffmpeg','-y','-loglevel','error','-i',AV+'/build/Psalm-91-Before-You-Walk-Out-the-Door-NEKO.mp4','-af','loudnorm=I=-14:TP=-2:LRA=11,alimiter=limit=0.8:level=disabled','-ar','48000','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',AV+'/build/Psalm-91-Neko-Voice-Final.mp4'])
print('DONE')
