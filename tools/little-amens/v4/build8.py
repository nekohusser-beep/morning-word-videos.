import json,subprocess,os,re
W=json.load(open('v3/words.json'))
# (label, clip id, in, out)
E=[('C01','acde5028',0,7.9),('C02','44a07f8d',0,7.9),('C03','3689231e',0,7.9),('C04','f1b9f378',0,7.9),('C05','e22b3c21',0,6.6),
   ('C06','7e2854a5',0,4.6),('C07','3c3e732e',0,7.9),('C08','be2d5848',0,7.9),('C09','52a61b9f',0,6.2),('C10','27d55d88',0.9,6.2),
   ('C11','d0fb9077',0,5.2),('C12','402f0cf7',1.9,7.2),('C13','b22cb28f',0,7.9),('C14','9e31f713',0,2.95),('C15','43f99ed7',0,7.9),
   ('C16','6f057c25',0,5.0),('C17','39a753e7',0,7.9),('C18','5d1a29b0',0,7.9),('C19','b4e1ddcf',0,7.0)]
import sys,pickle,numpy as np
def bursts(cid):
    F=pickle.load(open(f'v3/feat2/{cid}.pkl','rb'));e=F['e']/F['e'].max();fps=F['fps'];R=[];st=None
    for i,v in enumerate(list(e)+[0]):
        if v>0.12 and st is None: st=i
        if v<=0.12 and st is not None:
            if R and st-R[-1][1]<=0.10*fps: R[-1][1]=i
            else: R.append([st,i])
            st=None
    return [(x/fps,y/fps) for x,y in R if e[x:y].max()>=0.35]
INFO=json.load(open('v3/segH/info.json'))
lst=[]; t=0; caps=[]
FIX={'pip.':'Pip!','Ba':'Baa','-ah!':'','-men!':'-men!','-men.':'-men.','Momma!':'Mama!','Hahahaha.':'','Hahahahahaha.':'','Ah,':'Aaah...','ah,':'Aaah...','mmm,':'Mmmm.','Thank.':'Thank...','You.':'you.','he':'He','Say,':'Say...','say,':'say...','men.':'men!','men,':'men.'}
for lab,cid,a,b in E:
    var='F'; out=f'v3/segH/{lab}.mp4'; a=INFO[lab]['o0']; b=INFO[lab]['o1']
    dur=int(subprocess.run(['ffprobe','-v','error','-select_streams','v','-count_packets','-show_entries','stream=nb_read_packets','-of','csv=p=0',out],capture_output=True,text=True).stdout.strip().strip(','))/30
    lst.append(f"file '{os.path.abspath(out)}'")
    # captions: sentence chunks
    ws=[[w[0],max(w[1],a),w[2]] for w in W[cid] if w[2]>a+0.05 and w[1]<b-0.05]
    cur=[]; BU=bursts(cid); last=[-9]
    def flush():
        if not cur: return
        txt=' '.join(x[0] for x in cur).replace(' -','-').strip()
        if not txt: return
        txt=txt[0].upper()+txt[1:]
        ws=cur[0][1]; cand=[x for x in BU if x[0]>=max(ws-0.35,last[0]+0.05) and x[0]<=ws+(3.0 if last[0]<0 else 1.4)]
        inside=[x for x in BU if x[0]<ws-0.12 and x[1]>ws+0.05 and x[0]<=last[0]+0.01]
        on=ws if inside else (cand[0][0] if cand else ws)
        last[0]=on
        if on<a-0.02 or on>b-0.2: on=max(a,min(on,b-0.3))
        caps.append([t+on-a, t+max(cur[-1][2],on+0.4)-a, txt, t+dur])
    for w in ws:
        word=FIX.get(w[0],w[0])
        if word=='': continue
        cur.append([word,w[1],w[2]])
        if re.search(r'[.!?]$',word): flush(); cur=[]
        elif lab in ('C03','C05') and word.endswith(','):
            nx=[x for x in ws if x[1]>w[1]]
            if nx and nx[0][1]-w[1]>0.6: cur[-1][0]=word[:-1]+'.'; flush(); cur=[]
    flush()
    print(lab,var,cid,round(t,2),round(dur,2)); t+=dur
open('v3/list.txt','w').write('\n'.join(lst)); TOT=t
# extend caption ends
for i,c in enumerate(caps):
    nxt=caps[i+1][0] if i+1<len(caps) else TOT
    c[1]=min(max(c[1]+0.9,c[0]+1.3),nxt-0.16,c[3]-0.06)
def ts(x): return f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"
ass="""[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,Poppins,62,&H00FFFFFF,&H00FFFFFF,&H00703A1E,&H00703A1E,-1,0,0,0,100,100,0,0,3,14,0,2,60,60,22,1
Style: Title,Poppins,84,&H0047B5FF,&H00FFFFFF,&H00FFFFFF,&H50000000,-1,0,0,0,100,100,2,0,1,8,3,8,40,40,26,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ass+=f"Dialogue: 1,{ts(0.2)},{ts(3.2)},Title,,0,0,0,,{{\\fad(300,400)}}Little Amens\n"
for a,b,txt,_ in caps: ass+=f"Dialogue: 0,{ts(max(0,a-0.05))},{ts(b)},Word,,0,0,0,,{txt}\n"
open('v3/caps.ass','w').write(ass); json.dump(caps,open('v3/caps.json','w'))
for c in caps: print(round(c[0],2),round(c[1],2),c[2])
import numpy as np, wave
# exact join: each clip's sound is padded or cut to its own picture length in samples, so nothing drifts across cuts
# (stream-copy joining let short audio tails pull every later clip's sound early or late: v6 up to 0.12 s, v7 0.19 s)
segs=[l.split("'")[1] for l in lst]; pcm=[]
for p in segs:
    nf=int(subprocess.run(['ffprobe','-v','error','-select_streams','v','-count_packets','-show_entries','stream=nb_read_packets','-of','csv=p=0',p],capture_output=True,text=True).stdout.strip().strip(','))
    a=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',p,'-f','s16le','-ac','2','-ar','48000','-'],capture_output=True).stdout,np.int16).reshape(-1,2)
    n=int(round(nf*48000/30)); a=a[:n] if len(a)>=n else np.vstack([a,np.zeros((n-len(a),2),np.int16)]); pcm.append(a)
w=wave.open('v3/cat.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(48000); w.writeframes(np.vstack(pcm).tobytes()); w.close()
args=[]; fc=''
for i,p in enumerate(segs): args+=['-i',p]; fc+=f"[{i}:v]setpts=PTS-STARTPTS[v{i}];"
fc+=''.join(f'[v{i}]' for i in range(len(segs)))+f'concat=n={len(segs)}:v=1:a=0,fps=30[v]'
subprocess.run(['ffmpeg','-v','error','-y']+args+['-i','v3/cat.wav','-filter_complex',fc,'-map','[v]','-map',f'{len(segs)}:a','-c:v','libx264','-preset','veryfast','-crf','14','-pix_fmt','yuv420p','-c:a','pcm_s16le','v3/cat.mkv'],check=True)
subprocess.run(['ffmpeg','-v','error','-y','-i','v3/cat.mkv','-i','bed.wav','-filter_complex',
  f"[0:v]ass=v3/caps.ass,fade=t=in:st=0:d=0.5,fade=t=out:st={TOT-1.2:.2f}:d=1.2[v];[1:a]acompressor=threshold=-34dB:ratio=8:attack=5:release=120:makeup=4,dynaudnorm=f=75:g=5:m=10,volume=0.18,afade=t=in:st=0:d=1.5,afade=t=out:st={TOT-2:.2f}:d=2[bed];[0:a][bed]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
  '-map','[v]','-map','[a]','-t',f'{TOT:.2f}','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','little-amens-ep1-v8.mp4'],check=True)
print('TOTAL',TOT)
