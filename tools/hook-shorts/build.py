import sys,json,subprocess,re,os,textwrap
cfg=json.load(open(sys.argv[1])); S=cfg["dir"]; name=cfg["name"]
LV=S+"/lv/"; vo=cfg["vo"]  # dir with name_sNN.wav
text=cfg["text"]; parts=[x.strip() for x in re.split(r'(?<=[.!?:])\s+', text) if x.strip()]
dur=lambda f: float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
GAP=0.38
sd=[dur(f"{vo}/{name}_s{i:02d}.wav") for i in range(len(parts))]
starts=[];t=0
for d in sd: starts.append(t); t+=d+GAP
total=t
vs,ve=cfg["verse"]  # sentence index range of verse (inclusive)
# ---- shots: list per sentence of [src,t,(x)] ; verse sentences use cfg["verse_bg"]
W=f"{S}/hs_{name}"; os.makedirs(W,exist_ok=True)
clips=[]
def shot(src,st,d,out,x=None,zoom=False):
    if src.startswith("fire"): vf="scale=1080:1920"
    else:
        cx="(iw-506)/2" if x is None else str(x)
        vf=f"crop=506:900:{cx}:0,scale=1080:1920:flags=lanczos,unsharp=5:5:0.6"
    if zoom: vf+=",zoompan=z='min(zoom+0.0012,1.12)':d=1:s=1080x1920:fps=30"
    path=src if src.startswith("/") else (S+"/broll/"+src+".mp4" if src.startswith("fire") else LV+src+".mp4")
    subprocess.run(["ffmpeg","-loglevel","error","-y","-ss",str(st),"-i",path,"-t",f"{d:.3f}","-an","-vf",vf+",fps=30,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","18",out],check=True)
segs=[]  # (start,end,src,t,x)
i=0
for k,(st,d) in enumerate(zip(starts,sd)):
    span=d+GAP
    if vs<=k<=ve: continue
    sh=cfg["shots"][str(k)]
    n=len(sh); 
    for j,s in enumerate(sh):
        segs.append((st+span*j/n, st+span*(j+1)/n, s))
# verse block as one long shot
vst=starts[vs]; ven=starts[ve]+sd[ve]+GAP
segs.append((vst,ven,cfg["verse_bg"]))
segs.sort()
lst=[]
for n_,(a,b,s) in enumerate(segs):
    out=f"{W}/c{n_:02d}.mp4"; shot(s[0],s[1],b-a,out,s[2] if len(s)>2 else None, zoom=(n_==0)); lst.append(out)
open(f"{W}/l.txt","w").write("".join(f"file '{p}'\n" for p in lst))
subprocess.run(["ffmpeg","-loglevel","error","-y","-f","concat","-safe","0","-i",f"{W}/l.txt","-c","copy",f"{W}/v.mp4"],check=True)
# audio: concat sentences with gaps
af=[]; 
for k in range(len(parts)): af+=["-i",f"{vo}/{name}_s{k:02d}.wav"]
flt="".join(f"[{k}:a]aresample=48000,apad=pad_dur={GAP}[a{k}];" for k in range(len(parts)))+"".join(f"[a{k}]" for k in range(len(parts)))+f"concat=n={len(parts)}:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=9[a]"
subprocess.run(["ffmpeg","-loglevel","error","-y",*af,"-filter_complex",flt,"-map","[a]","-ar","48000",f"{W}/a.wav"],check=True)
# ---- ASS
def ts(t):
    t=max(t,0); return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
A=["[Script Info]","PlayResX: 1080","PlayResY: 1920","WrapStyle: 0","","[V4+ Styles]",
"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
"Style: Hook,Poppins,132,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,9,4,5,70,70,0,1",
"Style: Cap,Poppins,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,8,3,2,70,70,520,1",
"Style: CapY,Poppins,92,&H0000D7FF,&H0000D7FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,8,3,2,70,70,520,1",
"Style: Ref,Poppins,60,&H0047C6F2,&H0047C6F2,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,3,0,8,80,80,560,1",
"Style: Verse,DejaVu Serif,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,8,90,90,680,1",
"","[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
# hook = sentence 0 (and cfg hook_until sentences) as big centered text, words pop in
hk=cfg.get("hook_sents",1)
hend=starts[hk-1]+sd[hk-1]+GAP*0.6
A.append(f"Dialogue: 1,{ts(0)},{ts(hend)},Hook,,0,0,0,,{{\\fad(0,120)}}{cfg['hook_text']}")
# captions for other non-verse sentences, 3-word chunks spread by char length
for k in range(hk,len(parts)):
    if vs<=k<=ve: continue
    ws=parts[k].split(); tot=sum(len(w)+1 for w in ws); cur=starts[k]; chunks=[]; buf=[]; bst=cur
    for w in ws:
        d=sd[k]*(len(w)+1)/tot
        if not buf: bst=cur
        buf.append(w); cur+=d
        if len(buf)>=3 or re.search(r"[.,;:?!]$",w): chunks.append((bst,cur," ".join(buf))); buf=[]
    if buf: chunks.append((bst,cur," ".join(buf)))
    for j,(a,b,tx) in enumerate(chunks):
        b2=chunks[j+1][0] if j+1<len(chunks) else b+0.25
        sty="CapY" if any(x.lower().strip(".,?!") in cfg.get("yellow",[]) for x in tx.split()) else "Cap"
        A.append(f"Dialogue: 0,{ts(a)},{ts(b2)},{sty},,0,0,0,,{tx.upper()}")
# verse card
vt="\\N".join(textwrap.wrap(cfg["verse_text"],26))
A.append(f"Dialogue: 2,{ts(vst)},{ts(ven)},Ref,,0,0,0,,{{\\fad(200,150)}}{cfg['verse_ref'].upper()}")
A.append(f"Dialogue: 2,{ts(vst)},{ts(ven)},Verse,,0,0,0,,{{\\fad(250,150)}}{vt}")
open(f"{W}/s.ass","w").write("\n".join(A)+"\n")
out=f"{S}/cuts/{cfg['out']}"
vf=f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.55:t=fill:enable='between(t,{vst:.2f},{ven:.2f})',drawbox=x=0:y=0:w=iw:h=ih:color=black@0.25:t=fill:enable='lt(t,{hend:.2f})',subtitles={W}/s.ass:fontsdir=/usr/share/fonts/truetype/google-fonts"
subprocess.run(["ffmpeg","-loglevel","error","-y","-i",f"{W}/v.mp4","-i",f"{W}/a.wav","-vf",vf,"-map","0:v","-map","1:a","-shortest","-c:v","libx264","-preset","medium","-crf","19","-c:a","aac","-b:a","192k","-movflags","+faststart",out],check=True)
print(out,round(total,1),len(parts),"sentences")
