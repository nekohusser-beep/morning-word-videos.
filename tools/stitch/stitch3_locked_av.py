import json, subprocess, sys
sys.path.insert(0,'/home/claude/morning-word-videos./tools/stitch')
import stitch2 as S
cfg=json.load(open('cfg.json')); r=json.load(open('/tmp/st2n09/report.json'))
W,H,fps=1080,1920,30
segs=[]; cues=[]; t0=0.0
for i,c in enumerate(cfg['clips']):
    a,b=r['trims'][i]; s=r['scale'][i]; g=r['gains'][i]
    # align with original word times relative to trim start
    al=S.align_words(cfg['lines'][i], cfg['words'][i])
    crop=f"crop=min(iw\\,trunc(ih*{W}/{H}/2)*2):min(ih\\,trunc(iw*{H}/{W}/2)*2),"+("" if s==1.0 else f"crop=iw/{s}:ih/{s}:(iw-iw/{s})/2:(ih-ih/{s})/2,")
    L=b-a; n=round(L*fps); L=n/fps
    o=f'/tmp/rb_{i:02d}.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{a:.3f}','-t',f'{L+0.5:.4f}','-i',c,
      '-vf',f'fps={fps},{crop}scale={W}:{H}:flags=lanczos,setsar=1,format=yuv420p',
      '-af',f'aresample=48000,highpass=f=70,volume={g:.2f}dB,afade=t=in:d=0.02,afade=t=out:st={L-0.03:.3f}:d=0.03,apad=whole_dur={L:.4f}',
      '-t',f'{L:.4f}','-c:v','libx264','-crf','16','-preset','veryfast','-c:a','pcm_s16le','-ar','48000','-ac','2',o.replace('.mp4','.mov')],check=True)
    segs.append(o.replace('.mp4','.mov'))
    # caption cues: group words into short phrases (<=4 words)
    words=[(w,st-a+t0,en-a+t0) for (w,st,en) in al]
    k=0
    while k<len(words):
        grp=words[k:k+4]; 
        cues.append((max(grp[0][1],t0),min(grp[-1][2]+0.15,t0+L),' '.join(x[0] for x in grp))); k+=4
    t0+=L
open('/tmp/rb_list.txt','w').write(''.join(f"file '{p}'\n" for p in segs))
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i','/tmp/rb_list.txt','-c','copy','/tmp/rb_cat.mov'],check=True)
# fix overlapping cues
cues2=[]
for j,(s_,e_,tx) in enumerate(cues):
    if j+1<len(cues): e_=min(e_,cues[j+1][0])
    cues2.append((s_,e_,tx))
S.build_ass(cues2,W,H,'/tmp/rb_caps.ass',70,4,420)
subprocess.run(['ffmpeg','-v','error','-y','-i','/tmp/rb_cat.mov','-vf','ass=/tmp/rb_caps.ass','-af','loudnorm=I=-14:TP=-1.0:LRA=11','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','Derrick-Nov09-body-v2.mp4'],check=True)
print('total',t0)
