import json, subprocess, soundfile as sf, numpy as np, textwrap, sys, os
from PIL import Image, ImageDraw, ImageFont
SRC='/mnt/user-data/uploads/Claude-Work/kids-david-goliath/'
L=json.load(open('lines.json')); FPS=30; W,H=1080,1920
# line -> (clip, start offset)
clips=['v01','v02b','v03','v01','v05','v06b','v07','v08','v09','v10','v11','v12','v13','v14','v13']
offs=[0,0,0,4.0,0,0,0,0,0,0,0,0,0,0,4.0]
F=ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',70)
FV=ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',52)
FR=ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',40)
FB=ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',230)
def read_frames(path, start, dur):
    clipdur=7.9; avail=clipdur-start; speed=min(1.0, avail/dur)  # slow down if line longer than clip
    vf=f"setpts=PTS/{speed},fps={FPS},scale={W}:{H}:flags=lanczos"
    p=subprocess.run(['ffmpeg','-loglevel','error','-ss',str(start),'-i',path,'-vf',vf,'-t',str(dur),'-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True)
    a=np.frombuffer(p.stdout,np.uint8); n=len(a)//(W*H*3); return a[:n*W*H*3].reshape(n,H,W,3)
def chunks(text):
    w=text.split(); out=[]; cur=[]
    for x in w:
        cur.append(x)
        if len(cur)>=4 or x[-1] in '.!?,:': out.append(' '.join(cur)); cur=[]
    if cur: out.append(' '.join(cur))
    return out
def cap(d,txt,y=1420):
    for i,ln in enumerate(textwrap.wrap(txt,18)):
        tw=d.textlength(ln,font=F); d.text(((W-tw)/2,y+i*88),ln,font=F,fill='white',stroke_width=8,stroke_fill='black')
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','video_anim.mp4'],stdin=subprocess.PIPE)
for i,line in enumerate(L):
    dur=sf.info(f'a{i:02d}.wav').duration; speech=dur-0.25; n=round(dur*FPS)
    fr_all=read_frames(SRC+clips[i]+'.mp4',offs[i],dur)
    cs=chunks(line); lens=[len(c) for c in cs]; tot=sum(lens); bounds=np.cumsum([0]+[speech*l/tot for l in lens])
    for f in range(n):
        t=f/FPS; arr=fr_all[min(f,len(fr_all)-1)]; fr=Image.fromarray(arr); d=ImageDraw.Draw(fr)
        if i==9:
            box=Image.new('RGBA',(W,H),(0,0,0,0)); bd=ImageDraw.Draw(box); bd.rounded_rectangle((60,560,1020,1250),40,fill=(0,0,0,150)); fr.paste(box,(0,0),box); d=ImageDraw.Draw(fr)
            y=610
            for ln in textwrap.wrap(line.strip('"'),30): tw=d.textlength(ln,font=FV); d.text(((W-tw)/2,y),ln,font=FV,fill='white'); y+=72
            ref='1 Samuel 17:45 (ICB)'; tw=d.textlength(ref,font=FR); d.text(((W-tw)/2,y+30),ref,font=FR,fill=(255,214,90))
        else:
            k=int(np.searchsorted(bounds,min(t,speech-0.001),side='right'))-1; k=max(0,min(k,len(cs)-1)); cap(d,cs[k])
        if i==10 and t>speech-0.9:
            s='BAM!'; tw=d.textlength(s,font=FB); d.text(((W-tw)/2,380),s,font=FB,fill=(255,220,0),stroke_width=14,stroke_fill=(200,0,0))
        proc.stdin.write(fr.tobytes())
proc.stdin.close(); proc.wait(); print('ok')
