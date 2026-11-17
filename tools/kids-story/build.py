import json, subprocess, soundfile as sf, numpy as np, textwrap
from PIL import Image, ImageDraw, ImageFont
SRC='/mnt/user-data/uploads/Claude-Work/kids-david-goliath/'
L=json.load(open('lines.json')); FPS=30; W,H=1080,1920
imgs=['s01','s02','s03','s01','s05','s06','s07','s08','s09','s10','s11','s12','s13','s14','s13']
zooms=[(1.0,1.08),(1.08,1.0),(1.0,1.1),(1.18,1.28),(1.0,1.08),(1.08,1.0),(1.0,1.08),(1.0,1.1),(1.08,1.0),(1.0,1.06),(1.0,1.12),(1.12,1.0),(1.0,1.08),(1.0,1.08),(1.08,1.12)]
F=ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',70)
FV=ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',52)
FR=ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',40)
FB=ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',230)
cache={}
def base(n):
    if n not in cache:
        im=Image.open(SRC+n+'.jpg').convert('RGB')
        s=max(W/im.width,H/im.height); im=im.resize((round(im.width*s),round(im.height*s)),Image.LANCZOS)
        l=(im.width-W)//2; t=(im.height-H)//2; cache[n]=im.crop((l,t,l+W,t+H))
    return cache[n]
def frame(im,z):
    w,h=W/z,H/z; l=(W-w)/2; t=(H-h)/2
    return im.resize((W,H),Image.BILINEAR,box=(l,t,l+w,t+h))
def chunks(text):
    w=text.split(); out=[]; cur=[]
    for x in w:
        cur.append(x)
        if len(cur)>=4 or x[-1] in '.!?,:': out.append(' '.join(cur)); cur=[]
    if cur: out.append(' '.join(cur))
    return out
def cap(d,txt,y=1420):
    lines=textwrap.wrap(txt,18)
    for i,ln in enumerate(lines):
        tw=d.textlength(ln,font=F); d.text(((W-tw)/2,y+i*88),ln,font=F,fill='white',stroke_width=8,stroke_fill='black')
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','video.mp4'],stdin=subprocess.PIPE)
srt=[]; T=0.0
for i,line in enumerate(L):
    dur=sf.info(f'a{i:02d}.wav').duration; speech=dur-0.25; n=round(dur*FPS)
    cs=chunks(line); lens=[len(c) for c in cs]; tot=sum(lens); bounds=np.cumsum([0]+[speech*l/tot for l in lens])
    for k,c in enumerate(cs): srt.append((T+bounds[k],T+bounds[k+1],c))
    im=base(imgs[i]); z0,z1=zooms[i]
    for f in range(n):
        t=f/FPS; z=z0+(z1-z0)*f/max(n-1,1); fr=frame(im,z); d=ImageDraw.Draw(fr)
        if i==9:
            box=Image.new('RGBA',(W,H),(0,0,0,0)); bd=ImageDraw.Draw(box); bd.rounded_rectangle((60,560,1020,1250),40,fill=(0,0,0,150)); fr.paste(box,(0,0),box); d=ImageDraw.Draw(fr)
            v=line.strip('"'); y=610
            for ln in textwrap.wrap(v,30): tw=d.textlength(ln,font=FV); d.text(((W-tw)/2,y),ln,font=FV,fill='white'); y+=72
            ref='1 Samuel 17:45 (ICB)'; tw=d.textlength(ref,font=FR); d.text(((W-tw)/2,y+30),ref,font=FR,fill=(255,214,90))
        else:
            k=int(np.searchsorted(bounds,min(t,speech-0.001),side='right'))-1; k=max(0,min(k,len(cs)-1))
            cap(d,cs[k])
        if i==10 and t>speech-0.9:
            s='BAM!'; tw=d.textlength(s,font=FB); d.text(((W-tw)/2,380),s,font=FB,fill=(255,220,0),stroke_width=14,stroke_fill=(200,0,0))
        proc.stdin.write(fr.tobytes())
    T+=dur
proc.stdin.close(); proc.wait()
a=np.concatenate([sf.read(f'a{i:02d}.wav')[0] for i in range(len(L))]); sf.write('voice.wav',a,24000)
def ts(x): h=int(x//3600); m=int(x%3600//60); s=x%60; return f'{h:02d}:{m:02d}:{s:06.3f}'.replace('.',',')
open('captions.srt','w').write('\n'.join(f'{j+1}\n{ts(a)} --> {ts(b)}\n{c}\n' for j,(a,b,c) in enumerate(srt)))
print('frames done',T)
