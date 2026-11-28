import json, re, subprocess, sys, os, numpy as np, soundfile as sf
sys.path.insert(0,'.')
from comp_plan import *
import importlib
# reuse captions helpers without running the assembler's __main__
A=importlib.import_module('asm_ps91')
HEAD,chunks_txt,ts=A.HEAD,A.chunks_txt,A.ts
LIB='/home/claude/lib'
def speech_gaps(key):
    x,sr=sf.read(f'{SRC}/{key}.wav'); h=int(sr*0.02); nn=len(x)//h
    e=np.sqrt((x[:nn*h].reshape(nn,h)**2).mean(1)+1e-12); db=20*np.log10(e); thr=max(db.max()-34,-52); v=db>thr
    segs=[];s=None
    for i,f in enumerate(v):
        if f and s is None: s=i
        if not f and s is not None: segs.append((s,i)); s=None
    if s is not None: segs.append((s,nn))
    m=[]
    for a,b in segs:
        if m and (a-m[-1][1])*0.02<0.12: m[-1]=(m[-1][0],b)
        else: m.append((a,b))
    return [(m[i][1]*0.02,m[i+1][0]*0.02) for i in range(len(m)-1)]   # (end,next start) of internal pauses
def sentence_times(x):
    """absolute (local-timeline) start/end per sentence of one clip, boundaries snapped to real pauses"""
    sp=SPANS[x['key']]; on,en=sp['onset'],min(sp['end'],x['b']); sents=x['sent']
    if len(sents)==1: return [(x['t']+on-x['a'],x['t']+en-x['a'],sents[0])]
    L=[len(s) for s in sents]; tot=sum(L); cum=0; bounds=[]
    gaps=speech_gaps(x['key'])
    for i in range(len(sents)-1):
        cum+=L[i]; target=on+(en-on)*cum/tot
        cand=[g for g in gaps if g[1]-g[0]>=0.10 and g not in bounds]
        if cand: g=min(cand,key=lambda g:abs((g[0]+g[1])/2-target)); bounds.append(g)
        else: bounds.append((target,target))
    bounds.sort(); out=[]; s0=on
    for i,s in enumerate(sents):
        s1=bounds[i][0] if i<len(bounds) else en
        out.append((x['t']+s0-x['a'],x['t']+s1-x['a'],s))
        if i<len(bounds): s0=bounds[i][1]
    return out
HOOK=[(0.0,1.25,'BEFORE YOU WALK OUT','Hook'),(1.25,2.5,'THAT DOOR TODAY','Hook'),(2.5,3.9,'PRAY THIS FIRST','HookGold')]
def ass_open():
    L=[HEAD]
    def D(layer,a,b,style,text): L.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}\n")
    for i,(a,b,t,st) in enumerate(HOOK): D(3,a,b,st,(r"{\fad(0,60)}" if i==0 else r"{\fad(60,60)}")+t)
    D(3,4.4,8.2,'HookGold',r"{\fad(500,500)\fs110}PSALM 91")
    for x in OPENP:
        for a,b,s in sentence_times(x):
            cs=chunks_txt(s); tot=sum(len(c) for c in cs); t0=a
            for k,c in enumerate(cs):
                t1=t0+(b-a)*len(c)/tot; D(2,t0,t1+(0.2 if k==len(cs)-1 else 0),'Cap',c); t0=t1
    return ''.join(L)
def ass_close():
    L=[HEAD]
    def D(layer,a,b,style,text): L.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}\n")
    for x in CLOSEP:
        for a,b,s in sentence_times(x):
            cs=chunks_txt(s); tot=sum(len(c) for c in cs); t0=a
            for k,c in enumerate(cs):
                t1=t0+(b-a)*len(c)/tot; D(2,t0,t1+(0.2 if k==len(cs)-1 else 0),'Cap',c); t0=t1
    e0=CLOSE_END
    D(1,e0+0.3,CLOSE_LEN,'Title',r"{\fad(700,900)\pos(960,470)\fs100}TYPE  AMEN")
    D(1,e0+0.8,CLOSE_LEN,'Sub',r"{\fad(700,900)\pos(960,610)}BLESSED PRAYERS")
    return ''.join(L)
EQ='eq=brightness=-0.03:saturation=0.95:contrast=1.03'
def zoom_plan(x, first):
    """list of (rel_start,rel_end,zoom) inside the clip (rel to a); first clip of the opening changes zoom every 0.8 s for the first 3.2 s"""
    d=x['b']-x['a']
    if x['name'].startswith('type-amen'):
        cut=3.0-x['a']
        return [(0,cut,1.0),(cut,d,(1.35,'right'))]
    if first:
        z=[1.0,1.10,1.0,1.14,1.0]; cuts=[0,0.8,1.6,2.4,3.2]; segs=[]
        for i,c in enumerate(cuts):
            e=cuts[i+1] if i+1<len(cuts) else d
            segs.append((c,e,z[i]))
        return segs
    return None
def render(which):
    plan=OPENP if which=='open' else CLOSEP
    NF=1064 if which=='open' else int(round(CLOSE_LEN*30))
    D=NF/30.0
    ins=[];fc=[];labels=[]
    j=0
    for ci,x in enumerate(plan):
        f=f"{CL}/{x['key']}.mp4"; d=x['b']-x['a']
        zp=zoom_plan(x,which=='open' and ci==0)
        if zp is None: zp=[(0,d,1.0 if ci%2==0 else 1.08)]
        for (s0,s1,z) in zp:
            ins+=['-ss',f"{x['a']+s0:.3f}",'-t',f"{s1-s0:.3f}",'-i',f]
            if isinstance(z,tuple):
                zz=z[0]; W=int(round(1920*zz)); H=int(round(1080*zz)); CR=f"crop=1920:1080:{W-1920}:{(H-1080)//2}"
            else:
                W=int(round(1920*z)); H=int(round(1080*z)); CR="crop=1920:1080"
            fc.append(f"[{j}:v]setpts=PTS-STARTPTS,fps=30,split=3[ba{j}][bb{j}][bc{j}];[bb{j}]crop=112:24:470:184,gblur=sigma=7[bx{j}];[bc{j}]crop=120:24:980:182,gblur=sigma=7[by{j}];[ba{j}][bx{j}]overlay=470:184[bo{j}];[bo{j}][by{j}]overlay=980:182,scale={W}:{H}:flags=lanczos,{CR},{EQ},trim=duration={s1-s0:.3f},setpts=PTS-STARTPTS,setsar=1[s{j}]")
            labels.append((j,x['t']+s0,s1-s0)); j+=1
    # place segments on a black canvas timeline: tpad/overlay by concatenating with gap fillers (hold previous frame)
    # build with concat of segments; gaps between clips are filled by extending the previous segment (freeze via tpad)
    seq=[]
    for k,(jj,t,dd) in enumerate(labels):
        nxt=labels[k+1][1] if k+1<len(labels) else D
        need=nxt-t
        if need>dd+1e-3: fc.append(f"[s{jj}]tpad=stop_mode=clone:stop_duration={need-dd:.3f}[p{jj}]"); seq.append(f"[p{jj}]")
        else: fc.append(f"[s{jj}]trim=duration={max(need,0.04):.3f},setpts=PTS-STARTPTS[p{jj}]"); seq.append(f"[p{jj}]")
    body=''.join(seq)+f"concat=n={len(seq)}:v=1:a=0,tpad=stop_mode=clone:stop_duration=1.0[body]"; fc.append(body)
    if which=='open':
        fc.append(f"[body]trim=duration={D:.3f},setpts=PTS-STARTPTS,vignette=PI/4.6,fade=t=out:st={D-0.25:.2f}:d=0.25,ass=comp_open.ass[v]")
    else:
        # end card footage (Pexels 18749847 @ 86 s) after the last clip
        ec=f'{LIB}/18749847.mp4'
        fc.append(f"movie={ec}:seek_point=86,setpts=PTS-STARTPTS,fps=30,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,eq=brightness=-0.05:saturation=0.88:contrast=1.05,trim=duration={ENDCARD+0.6:.2f},setpts=PTS-STARTPTS,fps=30,settb=1/30[ecv]")
        fc.append(f"[body]trim=duration={CLOSE_END+0.6:.3f},setpts=PTS-STARTPTS,fps=30,settb=1/30[bd]")
        fc.append(f"[bd][ecv]xfade=transition=fade:duration=0.6:offset={CLOSE_END:.3f}[xx]")
        fc.append(f"[xx]trim=duration={D:.3f},setpts=PTS-STARTPTS,vignette=PI/4.6,fade=t=in:st=0:d=0.25,fade=t=out:st={D-1.5:.2f}:d=1.5,ass=comp_close.ass[v]")
    open(f'comp_{which}.ass','w').write(ass_open() if which=='open' else ass_close())
    cmd=['ffmpeg','-y','-loglevel','error']+ins+['-filter_complex',';'.join(fc),'-map','[v]','-r','30','-frames:v',str(NF),'-c:v','libx264','-crf','19','-preset','veryfast','-pix_fmt','yuv420p','-video_track_timescale','15360',f'comp_{which}.mp4']
    subprocess.check_call(cmd); print(which,'ok',round(D,3),flush=True)
if __name__=='__main__':
    for w in sys.argv[1:]: render(w)
