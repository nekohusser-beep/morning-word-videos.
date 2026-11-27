# Psalm 91 morning long assembler (adapted from the Thanksgiving assembler): split-card verses, footage per paragraph via plan.py.
import json, re, subprocess, os, sys, textwrap, numpy as np, soundfile as sf
sys.path.insert(0,'.')
tl=json.load(open('tl.json')); SECT=json.load(open('sections.json'))
OUT='Psalm-91-Before-You-Walk-Out-the-Door.mp4'
K=float(os.environ.get('K','0.9')); START=0.0; TAIL=6.0; LIB='/home/claude/lib'
def dur(f): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]).decode().strip())
def timeline(k):
    t=START; ev=[]; first=True
    for it in tl:
        if it['k']=='s':
            if not first: t+=0.7
            first=False
        elif it['k']=='n':
            ev.append(('n',t,t+it['d'],it['t'],it['f'],None,it['p'])); t+=it['d']+k*(0.62+(1.25 if it.get('para') else 0))
        else:
            t+=0.45; ev.append(('v',t,t+it['d'],it['t'],it['f'],it['ref'],it['p'])); t+=it['d']+k*2.4
    return t+TAIL,ev
TOTAL,ev=timeline(K)
P=sorted({e[6] for e in ev}); span={p:[min(e[1] for e in ev if e[6]==p),max(e[2] for e in ev if e[6]==p)] for p in P}
bnd={}
for j,p in enumerate(P): bnd[p]=0.0 if j==0 else (span[P[j-1]][1]+span[p][0])/2
bnd['end']=TOTAL
def seg(p): j=P.index(p); return bnd[p],(bnd[P[j+1]] if j+1<len(P) else TOTAL)
starts=sorted(int(k) for k in SECT)
chunks=[[p for p in P if starts[i]<=p<(starts[i+1] if i+1<len(starts) else 10**9)] for i in range(len(starts))]
def ts(x): x=max(0,x); return f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"
HEAD="""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Poppins,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,230,230,78,1
Style: Verse,DejaVu Serif,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,2.5,2,5,120,120,0,1
Style: Ref,Poppins,54,&H0057C8FF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,2,0,1,2.5,2,5,120,120,0,1
Style: Title,Poppins,170,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,6,0,1,3,3,5,100,100,0,1
Style: Sub,Poppins,62,&H0057C8FF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,3,0,1,2.5,2,5,100,100,0,1
Style: Hook,Poppins,104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,2,0,1,5,3,8,80,80,70,1
Style: HookGold,Poppins,104,&H0057C8FF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,2,0,1,5,3,8,80,80,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
def chunks_txt(s,mx=84):
    if len(s)<=mx: return [s]
    parts=re.split(r'(?<=,)\s+',s); out=[]; cur=''
    for p in parts:
        if len((cur+' '+p).strip())<=mx: cur=(cur+' '+p).strip()
        else:
            if cur: out.append(cur)
            while len(p)>mx:
                k=p.rfind(' ',0,mx); out.append(p[:k]); p=p[k+1:]
            cur=p
    if cur: out.append(cur)
    return out
HOOK=[(0.0,1.25,'BEFORE YOU WALK OUT','Hook'),(1.25,2.5,'THAT DOOR TODAY','Hook'),(2.5,3.9,'PRAY THIS FIRST','HookGold')]
RED=r"{\1c&H4D5AFF&}"; WHT=r"{\1c&HFFFFFF&}"
VERSE_WORDS=json.load(open('paras.json'))
RED_BY_PARA={p['i']:p.get('red',[]) for p in VERSE_WORDS}
def _norm(w): return re.sub(r"[^a-z0-9']","",w.lower())
def red_flags(words,keys):
    fl=[False]*len(words); nw=[_norm(w) for w in words]
    for k in keys:
        kw=[_norm(x) for x in k.split()]
        for i in range(len(nw)-len(kw)+1):
            if nw[i:i+len(kw)]==kw:
                for q in range(len(kw)): fl[i+q]=True
    return fl
def pages_for(txt,mx=250):
    if len(txt)<=mx: return [txt]
    n=-(-len(txt)//235); target=len(txt)/n
    sents=re.split(r'(?<=[.;:])\s+',txt); pages=[]; cur=''
    for sn in sents:
        cand=(cur+' '+sn).strip()
        if cur and len(pages)<n-1 and abs(len(cur)-target)<=abs(len(cand)-target): pages.append(cur); cur=sn
        else: cur=cand
    pages.append(cur)
    return pages
def verse_card(e,o):
    txt,ref,pidx=e[3],e[5],e[6]; keys=RED_BY_PARA.get(pidx,[])
    pages=pages_for(txt); tot=sum(len(p) for p in pages); a=e[1]-0.45; b=e[2]+0.6; out=[]; t0=a
    for k,pg in enumerate(pages):
        t1=t0+(b-a)*len(pg)/tot
        words=pg.split(); fl=red_flags(words,keys)
        fs=60; lh=62; W=28
        lines=[]; cur=[]; clen=0
        for wi,w in enumerate(words):
            if cur and clen+1+len(w)>W: lines.append(cur); cur=[]; clen=0
            cur.append(wi); clen+=len(w)+(1 if clen else 0)
        if cur: lines.append(cur)
        n=len(lines); body=[]
        for ln in lines:
            seg=[]; prev=False
            for wi in ln:
                if fl[wi]!=prev: seg.append((RED if fl[wi] else WHT)); prev=fl[wi]
                seg.append(words[wi]+' ')
            if prev: seg.append(WHT)
            body.append(''.join(seg).rstrip())
        fin=0.45 if k==0 else 0.2; fout=0.45 if k==len(pages)-1 else 0.2
        top=540-n*lh/2
        if k==0:
            out.append(f"Dialogue: 0,{ts(t0-o)},{ts(b-o)},Cap,,0,0,0,,{{\\an7\\pos(0,0)\\1c&H000000&\\1a&H30&\\bord0\\shad0\\fad(450,450)\\p1}}m 900 0 l 1920 0 1920 1080 900 1080{{\\p0}}\n")
            out.append(f"Dialogue: 0,{ts(t0-o)},{ts(b-o)},Cap,,0,0,0,,{{\\an7\\pos(0,0)\\1c&H57C8FF&\\1a&H00&\\bord0\\shad0\\fad(450,450)\\p1}}m 900 0 l 908 0 908 1080 900 1080{{\\p0}}\n")
        out.append(f"Dialogue: 1,{ts(t0-o)},{ts(t1-o)},Ref,,0,0,0,,{{\\an4\\fad({int(fin*1000)},{int(fout*1000)})\\pos(980,{top-60:.0f})}}{ref.upper()}\n")
        out.append(f"Dialogue: 1,{ts(t0-o)},{ts(t1-o)},Verse,,0,0,0,,{{\\an4\\fad({int(fin*1000)},{int(fout*1000)})\\fs{fs}\\pos(980,{top+n*lh/2+18:.0f})}}"+r"\N".join(body)+"\n")
        t0=t1
    return out
def ass_for(i):
    o=bnd[chunks[i][0]]; e1=bnd[chunks[i+1][0]] if i+1<len(chunks) else TOTAL
    L=[HEAD]
    def D(layer,a,b,style,text): L.append(f"Dialogue: {layer},{ts(a-o)},{ts(b-o)},{style},,0,0,0,,{text}\n")
    if i==0:
        for a,b,t,st in HOOK: D(3,a,b,st,r"{\fad(60,60)}"+t)
        D(3,4.4,8.2,'HookGold',r"{\fad(500,500)\fs84}PSALM 91")
    if i==len(chunks)-1:
        D(1,TOTAL-5.4,TOTAL,'Title',r"{\fad(700,900)\pos(960,470)\fs100}TYPE  AMEN")
        D(1,TOTAL-4.9,TOTAL,'Sub',r"{\fad(700,900)\pos(960,610)}BLESSED PRAYERS")
    for e in ev:
        if not (o<=e[1]<e1): continue
        if e[0]=='n':
            cs=chunks_txt(e[3]); tot=sum(len(c) for c in cs); a=e[1]
            for k,c in enumerate(cs):
                b=a+(e[2]-e[1])*len(c)/tot; D(2,a,b+(0.2 if k==len(cs)-1 else 0),'Cap',c); a=b
        else:
            L.extend(verse_card(e,o))
    return ''.join(L)
def plan_for(p):
    D=seg(p)[1]-seg(p)[0]; specs=PLAN[p]; fixed=sum(s[2] for s in specs if len(s)>2 and s[2]); free=[s for s in specs if not(len(s)>2 and s[2])]
    rest=max(0.5,D-fixed); out=[]
    for s in specs:
        d=s[2] if len(s)>2 and s[2] else rest/len(free)
        out.append((s[0],s[1] if len(s)>1 and s[1] is not None else 0.5,d))
    return out
def build_chunk(i):
    ps=chunks[i]; a0=bnd[ps[0]]; a1=bnd[chunks[i+1][0]] if i+1<len(chunks) else TOTAL; Dc=a1-a0
    items=[]
    for p in ps:
        # stretch last clip of the paragraph so the sum matches the paragraph segment exactly
        b0,b1=seg(p); pl=plan_for(p); sc=(b1-b0)/sum(x[2] for x in pl); items+= [(c,ss,d*sc) for c,ss,d in pl]
    n=len(items); X=[min(0.8,0.4*min(items[k][2],items[k+1][2])) if k<n-1 else 0 for k in range(n)]
    X=[0.1 if (k<n-1 and min(items[k][2],items[k+1][2])<1.6) else x for k,x in enumerate(X)]
    ins=[];fc=[];used={}
    for k,(c,ss,d) in enumerate(items):
        f=f'{LIB}/{c}.mp4'; Ld=dur(f); R=d+X[k]+0.05
        u=used.get(c,0); used[c]=u+1; st=ss+u*(R+0.5)
        if Ld-st<R/1.7: st=0.2
        avail=Ld-st-0.12; F=max(1.0,R/avail)
        if F==1.0 and avail>R*1.25 and d>=3.0: F=1.25
        if F>1.7: print('WARN slow',c,'need',round(R,1),'avail',round(avail,1),'F',round(F,2),flush=True)
        ins+=['-ss',f'{st:.2f}','-t',f'{R/F+0.4:.2f}','-i',f]
        EQ='eq=brightness=0.02:saturation=0.9:contrast=1.0' if c in (15671645,) else 'eq=brightness=-0.05:saturation=0.88:contrast=1.05'
        fc.append(f"[{k}:v]setpts={F:.4f}*(PTS-STARTPTS),fps=30,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,{EQ},trim=duration={R:.3f},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[c{k}]")
    last='c0'; cum=0
    for k in range(1,n):
        cum+=items[k-1][2]; fc.append(f"[{last}][c{k}]xfade=transition=fade:duration={X[k-1]:.3f}:offset={cum:.3f}[x{k}]"); last=f'x{k}'
    open(f'chunk{i}.ass','w').write(ass_for(i))
    fi="" if i==0 else ",fade=t=in:st=0:d=0.25"
    fo=f",fade=t=out:st={Dc-1.5:.2f}:d=1.5" if i==len(chunks)-1 else f",fade=t=out:st={Dc-0.25:.2f}:d=0.25"
    fc.append(f"[{last}]trim=duration={Dc:.3f},setpts=PTS-STARTPTS,vignette=PI/4.6{fi}{fo},ass=chunk{i}.ass[v]")
    cmd=['ffmpeg','-y','-loglevel','error']+ins+['-filter_complex',';'.join(fc),'-map','[v]','-r','30','-c:v','libx264','-crf','19','-preset','veryfast','-pix_fmt','yuv420p','-video_track_timescale','15360',f'tmp_chunk{i}.mp4']
    subprocess.check_call(cmd); os.rename(f'tmp_chunk{i}.mp4',f'chunk{i}.mp4'); print('chunk',i,round(Dc,2),n,'clips',flush=True)
def audio():
    sr=24000; v=np.zeros(int(TOTAL*sr)+sr,dtype=np.float32)
    for e in ev:
        a,_=sf.read(e[4],dtype='float32'); p=int(e[1]*sr); v[p:p+len(a)]+=a
    sf.write('voice.wav',v[:int(TOTAL*sr)],sr)
    SR=44100; N=int(TOTAL*SR); tt=np.arange(N)/SR; m=np.zeros(N,dtype=np.float32)
    nf=lambda n:440*2**((n-69)/12)
    CH=[[38,45,50,53,57],[34,41,46,50,53],[41,48,53,57,60],[36,43,48,52,55]]; CD=12.0
    rng=np.random.default_rng(3)
    for ci in range(int(TOTAL/CD)+1):
        a=int(ci*CD*SR); b=min(N,int((ci*CD+CD+4)*SR))
        if a>=N: break
        x=tt[a:b]-ci*CD; env=np.clip(x/4,0,1)*np.clip((CD+4-x)/4,0,1); env=env**1.5
        for j,n in enumerate(CH[ci%4]):
            f=nf(n); g=0.9/(1+j*0.35)
            for det in (-0.35,0,0.4):
                m[a:b]+=(g*env*np.sin(2*np.pi*(f+det)*x+rng.random()*6)*(1+0.15*np.sin(2*np.pi*0.11*x+j))).astype(np.float32)
            m[a:b]+=(0.18*g*env*np.sin(2*np.pi*2*f*x)).astype(np.float32)
        for q in range(2):
            n=CH[ci%4][rng.integers(2,5)]+12+(12 if rng.random()<.3 else 0); s0=a+int((1.5+q*5.5+rng.random()*1.5)*SR); e0=min(N,s0+6*SR)
            if s0<N and s0/SR < TOTAL-9:
                y=np.arange(e0-s0)/SR; f=nf(n)
                m[s0:e0]+=(1.3*np.exp(-y*0.9)*(np.sin(2*np.pi*f*y)+0.3*np.sin(2*np.pi*2*f*y)*np.exp(-y*2))*np.clip(y/0.02,0,1)).astype(np.float32)
    m/=np.abs(m).max()*1.1; fi=np.clip(tt/2.5,0,1)*np.clip((TOTAL-tt)/8,0,1); sf.write('music_raw.wav',m*fi,SR)
    subprocess.check_call(f"ffmpeg -y -loglevel error -i voice.wav -i music_raw.wav -filter_complex \"[1:a]lowpass=f=2600,aecho=0.8:0.7:90|180|330:0.35|0.25|0.18,aformat=channel_layouts=stereo,volume=-19dB[m];[0:a]highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,volume=3dB,aformat=channel_layouts=stereo[v];[v][m]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,atrim=duration={TOTAL:.2f}[a]\" -map \"[a]\" -ar 48000 mix.wav",shell=True)
if __name__=='__main__':
    a=sys.argv[1]
    if a=='t':
        print('TOTAL',round(TOTAL,1))
        for i,c in enumerate(chunks): print('chunk',i,'paras',c[0],'-',c[-1],'dur',round((bnd[chunks[i+1][0]] if i+1<len(chunks) else TOTAL)-bnd[c[0]],1))
        for p in P: print(' p',p,round(seg(p)[1]-seg(p)[0],1),'s')
    else:
        from plan import PLAN
        if a=='audio': audio()
        elif a=='join':
            open('list.txt','w').write(''.join(f"file 'chunk{i}.mp4'\n" for i in range(len(chunks))))
            subprocess.check_call("ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy vid.mp4 && ffmpeg -y -loglevel error -i vid.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart tmp_out.mp4 && mv tmp_out.mp4 "+OUT,shell=True)
        else:
            for i in a.split(','): build_chunk(int(i))
