# captions.srt + chapter starts for the Neko-avatar composite, straight from the burned-in .ass files (identical to what is on screen).
import re, subprocess
B='/home/claude/ps91/build'; FPS=30.0
def nf(f): return int(subprocess.check_output(f"ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 {B}/{f}",shell=True))
T_OPEN=nf('comp_open_709.mp4')/FPS; ch=[nf(f'chunk{i}.mp4')/FPS for i in range(1,7)]; T_MID=sum(ch)
offs=[('comp_open.ass',0.0)]; t=T_OPEN
for i in range(1,7): offs.append((f'chunk{i}.ass',t)); t+=ch[i-1]
offs.append(('comp_close.ass',T_OPEN+T_MID))
def sec(s):
    h,m,r=s.split(':'); return int(h)*3600+int(m)*60+float(r)
def ts(x):
    ms=int(round(max(0,x)*1000)); h,r=divmod(ms,3600000); m,r=divmod(r,60000); s,ms=divmod(r,1000); return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
cues=[]
for f,o in offs:
    for l in open(f'{B}/{f}'):
        if not l.startswith('Dialogue:'): continue
        p=l.rstrip('\n').split(',',9)
        layer,st,en,style,text=int(p[0].split(':')[1]),p[1],p[2],p[3],p[9]
        if style!='Cap' or layer!=2: continue
        text=re.sub(r'\{[^}]*\}','',text).replace('\\N','\n').strip()
        if text: cues.append((o+sec(st),o+sec(en),text))

import json, math
tl=json.load(open(f'{B}/tl.json')); K=0.9; t=0.0; first=True
SEAM1=35.4525; WARP=1.0001475
def newt(x): return T_OPEN+(x-SEAM1)/WARP
vcues=[]
for it in tl:
    if it['k']=='s':
        if not first: t+=0.7
        first=False
    elif it['k']=='n':
        t+=it['d']+K*(0.62+(1.25 if it.get('para') else 0))
    else:
        t+=0.45; a=t; b=t+it['d']; t+=it['d']+K*2.4
        txt=re.sub(r'\s+',' ',it['t']).strip(); words=txt.split()
        k=max(1,math.ceil(len(txt)/80))
        # balanced groups of ~equal characters
        tot=sum(len(w)+1 for w in words); g=[];cur=[];done=0
        for w in words:
            if cur and len(g)<k-1 and done+sum(len(x)+1 for x in cur)+len(w)/2>tot/k*(len(g)+1):
                done+=sum(len(x)+1 for x in cur); g.append(cur); cur=[]
            cur.append(w)
        g.append(cur)
        L=sum(len(' '.join(x)) for x in g); pos=a
        for x in g:
            tx=' '.join(x); d=(b-a)*len(tx)/L
            vcues.append((newt(pos),newt(pos+d),tx)); pos+=d
cues=sorted(cues+vcues)
out=[]
for n,(a,b,tx) in enumerate(cues,1):
    # keep each cue on at most two balanced lines of <=42 chars
    w=tx.split(); 
    if len(tx)>42:
        best=None
        for i in range(1,len(w)):
            x=' '.join(w[:i]); y=' '.join(w[i:])
            if max(len(x),len(y))<=42:
                d=abs(len(x)-len(y))
                if best is None or d<best[0]: best=(d,x+'\n'+y)
        tx=best[1] if best else tx
    out.append(f"{n}\n{ts(a)} --> {ts(b)}\n{tx}\n")
open(f'{B}/pack/captions.srt','w').write('\n'.join(out)+'\n')
print(len(cues),'cues; last ends',round(cues[-1][1],2),'; total',round(T_OPEN+T_MID+nf('comp_close_709.mp4')/FPS,3))
marks={'dwell':'Here is how it starts.','trap':'Verses 3 and 4.','hours':'Verses 5 through 8.','refuge':'Back to the psalm.','angels':'Verses 11 through 13.','love':'Now listen, because in verse 14','pray':'So here is the prayer.'}
for k,v in marks.items():
    for a,b,tx in cues:
        if tx.replace('\n',' ').startswith(v): print(f"{k:7s} {a:8.2f}  {int(a)//60}:{int(a)%60:02d}"); break
