import sys,json,subprocess,os,re
cfg=json.load(open(sys.argv[1]))
src=cfg["src"]; segs=cfg["segs"]; out=cfg["out"]; hook=cfg["hook"]; words=cfg["words"]  # words: [[s,e,text],...] source time
SC="/tmp/claude-0/-home-claude-morning-word-videos-/8b98f658-3789-5529-bc4a-55ec00ad1604/scratchpad/cuts"
font="/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
# map words into output timeline, chunk into <=4 words
off=0; chunks=[]
for seg in segs:
    a,b=seg[0],seg[1]
    if len(seg)>2: off+=b-a; continue
    ws=[w for w in words if w[0]>=a-0.05 and w[1]<=b+0.15]
    cur=[]
    for w in ws:
        cur.append(w)
        if len(cur)>=4 or re.search(r"[.,;:?!]$",w[2]):
            chunks.append((cur[0][0]-a+off,cur[-1][1]-a+off," ".join(x[2] for x in cur))); cur=[]
    if cur: chunks.append((cur[0][0]-a+off,cur[-1][1]-a+off," ".join(x[2] for x in cur)))
    off+=b-a
def ts(t):
    t=max(t,0); h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"
ass=["[Script Info]","PlayResX: 1080","PlayResY: 1920","","[V4+ Styles]",
"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
"Style: Cap,Poppins,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,2,2,70,70,560,1",
"Style: Hook,Poppins,80,&H0000D7FF,&H0000D7FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,2,8,60,60,230,1",
"","[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
total=off
ass.append(f"Dialogue: 0,{ts(0)},{ts(total)},Hook,,0,0,0,,{hook}")
for i,(s,e,t) in enumerate(chunks):
    nxt=chunks[i+1][0] if i+1<len(chunks) else e+0.3
    ass.append(f"Dialogue: 0,{ts(s)},{ts(min(max(e,s+0.35),nxt))},Cap,,0,0,0,,{t.upper()}")
assf=out+".ass"; open(assf,"w").write("\n".join(ass)+"\n")
parts=[]
for i,seg in enumerate(segs):
    a,b=seg[0],seg[1]; p=f"{SC}/_p{i}.mp4"; d=b-a
    fg="crop=1350:1080:(iw-1350)/2:0,scale=1080:-2" if len(seg)>2 else "crop=1100:880:(iw-1100)/2:20,scale=1080:-2"
    pv=("split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=28:2,eq=brightness=-0.2[bg];"
        "[b]"+fg+"[fg];[bg][fg]overlay=0:(H-h)/2-60")
    subprocess.run(["ffmpeg","-loglevel","error","-y","-ss",str(a),"-i",src,"-t",str(d),"-vf",pv,
      "-af",f"afade=t=in:d=0.06,afade=t=out:st={max(d-0.08,0)}:d=0.08","-r","30","-c:v","libx264","-preset","veryfast","-crf","17","-c:a","aac","-ar","48000",p],check=True)
    parts.append(p)
lst=out+".txt"; open(lst,"w").write("".join(f"file '{p}'\n" for p in parts))
tmp=out+".cat.mp4"
subprocess.run(["ffmpeg","-loglevel","error","-y","-f","concat","-safe","0","-i",lst,"-c","copy",tmp],check=True)
# fg: crop off the burned caption band (bottom ~17%) and the sides, fill more height
vf=("[0:v]subtitles="+assf+":fontsdir=/usr/share/fonts/truetype/google-fonts[v]")
subprocess.run(["ffmpeg","-loglevel","error","-y","-i",tmp,"-filter_complex",vf,"-map","[v]","-map","0:a",
  "-af","loudnorm=I=-14:TP=-1.5:LRA=11","-c:v","libx264","-preset","medium","-crf","20","-c:a","aac","-b:a","160k","-movflags","+faststart",out],check=True)
os.remove(tmp)
print(out, subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",out],capture_output=True,text=True).stdout.strip())
