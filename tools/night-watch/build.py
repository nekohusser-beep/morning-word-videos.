import json, re, subprocess, numpy as np, soundfile as sf
SR=24000
tl=json.load(open('v/tl.json'))
# voice start times (s) on the final timeline
starts=[0.4]
gaps=[0.8,0.45,0.6,1.0,0.5,1.0,1.0,1.1,0.7,0.6]
for i,g in enumerate(gaps): starts.append(starts[-1]+tl[i]['dur']+g)
TOTAL=59.7
print([round(s,2) for s in starts], 'last end', round(starts[-1]+tl[-1]['dur'],2))
# ---- voice track
voice=np.zeros(int(TOTAL*SR),dtype=np.float32)
speech=[]  # (start,end) trimmed speech region per line
for i,s in enumerate(starts):
    a,_=sf.read(f'v/l{i+1:02d}.wav',dtype='float32')
    thr=10**(-45/20); idx=np.where(np.abs(a)>thr)[0]
    lo,hi=idx[0],idx[-1]
    o=int(s*SR); voice[o:o+len(a)]+=a
    speech.append((s+lo/SR, s+hi/SR))
# ---- code-made pad under the voice
rng=np.random.default_rng(7); t=np.arange(len(voice))/SR
pad=np.zeros_like(voice)
for f,amp,lfo,ph in [(110.0,1.0,0.07,0.0),(164.81,0.8,0.09,1.3),(220.0,0.6,0.11,2.1),(329.63,0.35,0.13,0.7)]:
    pad+=amp*np.sin(2*np.pi*f*t+0.3*np.sin(2*np.pi*0.05*t+ph))*(0.65+0.35*np.sin(2*np.pi*lfo*t+ph))
br=np.cumsum(rng.standard_normal(len(t)).astype(np.float32)); br-=np.convolve(br,np.ones(2400)/2400,mode='same'); br/=np.max(np.abs(br))
pad=pad/np.max(np.abs(pad))*0.5+br*0.35
fade=np.minimum(1,np.minimum(t/3.0,(TOTAL-t)/3.5)).astype(np.float32)
pad=(pad*fade).astype(np.float32)
sf.write('pad_raw.wav',pad,SR); sf.write('voice_raw.wav',voice,SR)
# ---- captions (ASS) 1080x1920
G={1:["If you're awake","right now while","the rest of","the street is asleep,","this one's for you."],
2:["My soul waiteth","for the LORD","more than they","that watch for","the morning:"],
3:["I say, more than","they that watch for","the morning."],
4:[("That's Psalm","That's Psalm"),("130:6.","one hundred thirty, verse six.")],
5:["A night watchman","stood on the wall","for hours, and","the only thing","he wanted","was daylight."],
6:["I've worked enough","overnights to know","that wait,","with the clock","crawling toward","morning."],
7:["The writer says","he waits on God","harder than that","watchman waits","on the sun."],
8:["And the sun","always came up.","Every night that","watchman ever stood,","the morning","showed up."],
9:["Father, for everybody","still up tonight,","at work,","at a bedside,","or just wide awake,","be near them."],
10:["In Jesus' name, amen."],
11:["Morning's coming.","Follow so the","Word finds you","on the long nights.","Have a blessed day."]}
def w(g): 
    sp=g if isinstance(g,str) else g[1]
    return len(re.sub(r'[^A-Za-z0-9]','',sp))+ (4 if sp.rstrip()[-1] in ',:' else 0)+(7 if sp.rstrip()[-1] in '.?!' else 0)
ev=[]
for ln,groups in G.items():
    s,e=speech[ln-1]; ws=[w(g) for g in groups]; tot=sum(ws); cur=s
    for g,wt in zip(groups,ws):
        d=(e-s)*wt/tot; txt=g if isinstance(g,str) else g[0]
        ev.append((cur,cur+d,txt)); cur+=d
def ts(x):
    h=int(x//3600); m=int(x%3600//60); sec=x%60; return f"{h}:{m:02d}:{sec:05.2f}"
hdr="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Cap,Poppins,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6.3,0,2,60,60,330,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
with open('cap.ass','w') as f:
    f.write(hdr)
    for i,(a,b,t) in enumerate(ev):
        if i+1<len(ev) and ev[i+1][0]-b<0.01: pass
        e=b if (i+1<len(ev) and ev[i+1][0]-b<0.30) else b+0.12
        f.write(f"Dialogue: 0,{ts(a)},{ts(e)},Cap,,0,0,0,,{{\\fad(60,40)}}{t}\n")
json.dump({'starts':starts,'speech':speech,'events':ev},open('timeline.json','w'),indent=1)
# SRT
with open('nightwatch.srt','w') as f:
    def st(x): 
        h=int(x//3600); m=int(x%3600//60); s=x%60; return f"{h:02d}:{m:02d}:{int(s):02d},{int((s%1)*1000):03d}"
    for i,(a,b,t) in enumerate(ev,1): f.write(f"{i}\n{st(a)} --> {st(b)}\n{t}\n\n")
print(len(ev),'caption groups')
