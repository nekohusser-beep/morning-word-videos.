# Psalm 91 avatar version: Neko's Flow avatar opens (o1-o5) and closes (c1-c7) the Starhead-passed master; middle = master 35.453..406.24 s.
import json,subprocess,re,os,sys
import sherpa_onnx, soundfile as sf, numpy as np
os.chdir('/home/claude/ps91av')
B=json.load(open('bnd.json')); MS=B['bnd']['2']; ME=B['bnd']['28']
MASTER=os.environ.get('MASTER','/home/claude/ps91m/Psalm-91-Before-You-Walk-Out-the-Door.mp4')
d='/home/claude/vet/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'
R=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{d}/encoder.int8.onnx',decoder=f'{d}/decoder.int8.onnx',joiner=f'{d}/joiner.int8.onnx',tokens=f'{d}/tokens.txt',model_type='nemo_transducer',num_threads=2)
OPEN=['o1','o2','o3','o4','o5']; CLOSE=['c1','c2','c3','c4','c5','c6','c7']
CUT_END={'c6':6.28}
HOLD={'c6':1.2}  # quiet beat after the prayer's Amen so the closer's 'Type amen' does not sound like an echo
def words(clip):
    subprocess.check_call(['ffmpeg','-y','-loglevel','error','-i',f'clip_{clip}.mp4','-vn','-ac','1','-ar','16000','/tmp/w.wav'])
    a,sr=sf.read('/tmp/w.wav',dtype='float32'); s=R.create_stream(); s.accept_waveform(sr,a); R.decode_stream(s)
    W=[]
    for tok,t in zip(s.result.tokens,s.result.timestamps):
        if tok.startswith(' ') or not W: W.append([tok.strip(),t])
        else: W[-1][0]+=tok
    W=[w for w in W if re.search(r'[A-Za-z]',w[0])]
    # energy: true end of speech
    env=np.convolve(np.abs(a),np.ones(320)/320,'same'); thr=max(0.01,env.max()*0.06)
    return W,a,sr,env,thr
def seg_bounds(clip,W,a,sr,env,thr):
    st=max(0.0,W[0][1]-0.3)
    last=W[-1][1]; lim=CUT_END.get(clip,len(a)/sr-0.05)
    idx=np.where(env[int(last*sr):int(lim*sr)]>thr)[0]
    en=(last+ (idx[-1]/sr if len(idx) else 0.4)+0.35)
    return st,min(en,lim)
TXT={'o1':"Before you walk out that door today, give me a few minutes. You already know what's out there.",
'o2':"The email you've been dreading. The drive. The conversation you keep putting off.",
'o3':"And you're about to walk into all of it with nothing between you and the day but a cup of coffee.",
'o4':"This psalm is for the person standing at that door. People have prayed it in hospital hallways, before shifts,",
'o5':"and on the way to jobs they were scared to lose. Pray it with me, and then go.",
'c1':"So here is the prayer. Pray it out loud if you can.",
'c2':"Father, I am stepping out the door, and I am putting this day under your wing.",
'c3':"Cover my house while I am gone. Cover the ones I love, wherever they are right now.",
'c4':"When a trap is set, show me before I step. When fear comes, remind me where I dwell.",
'c5':"Send your angels ahead of me, and let me come home tonight with a thankful heart.",
'c6':"I ask it in the name of Jesus Christ. Amen.",
'c7':"Type amen, and send this to a friend who needs it. Have a blessed day, and remember the Word for today."}
X=0.3  # crossfade between avatar clips
def build_part(name,clips,tail=0.0):
    info=[]
    for c in clips:
        W,a,sr,env,thr=words(c); st,en=seg_bounds(c,W,a,sr,env,thr)
        tw=TXT[c].split()
        if len(tw)!=len(W): print('WARN word count',c,len(tw),len(W),file=sys.stderr)
        times=[w[1]-st for w in W]; info.append((c,st,en,tw,times))
    # video/audio graph
    ins=[];fc=[];cum=0;offs=[]
    for k,(c,st,en,tw,times) in enumerate(info):
        D0=en-st; hold=tail if (k==len(info)-1) else HOLD.get(c,0)
        ins+=['-ss',f'{st:.3f}','-t',f'{D0:.3f}','-i',f'clip_{c}.mp4']
        D=D0 if k==len(info)-1 else D0+hold
        fc.append(f"[{k}:v]fps=30,scale=1920:1080:flags=lanczos,unsharp=5:5:0.6,setsar=1,format=yuv420p,trim=duration={D0:.3f},setpts=PTS-STARTPTS"+(f",tpad=stop_mode=clone:stop_duration={hold:.2f}" if hold else "")+f"[v{k}]")
        fc.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={D0:.3f},asetpts=PTS-STARTPTS"+(f",apad=pad_dur={hold:.2f}" if hold else "")+f"[a{k}]")
        offs.append(cum); cum+=D-X
        if k==len(info)-1: cum+=0  # tail added below
    total=cum+X+tail
    lv='v0';la='a0';o=0
    for k in range(1,len(info)):
        o=offs[k]; fc.append(f"[{lv}][v{k}]xfade=transition=fade:duration={X}:offset={o:.3f}[vx{k}]"); lv=f'vx{k}'
        fc.append(f"[{la}][a{k}]acrossfade=d={X}:c1=tri:c2=tri[ax{k}]"); la=f'ax{k}'
    return info,offs,total,ins,fc,lv,la
HEAD=open('/home/claude/ps91m/asm_ps91.py').read().split('HEAD="""')[1].split('"""')[0]
def ts(x): x=max(0,x); return f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"
def caps(info,offs,extra):
    L=[HEAD]; CU=[]
    for (c,st,en,tw,times),o in zip(info,offs):
        # group words into cues of <=66 chars, split at punctuation when possible
        cues=[];cur=[]
        for i,w in enumerate(tw):
            if cur and len(' '.join(tw[j] for j in cur+[i]))>66: cues.append(cur); cur=[]
            cur.append(i)
            if re.search(r'[.?!]$',w) and len(' '.join(tw[j] for j in cur))>28: cues.append(cur); cur=[]
        if cur: cues.append(cur)
        for q,cu in enumerate(cues):
            a=o+times[cu[0]]-0.05
            b=(o+times[cues[q+1][0]]-0.08) if q+1<len(cues) else o+min(en-st, times[cu[-1]]+0.9)
            txt=' '.join(tw[j] for j in cu)
            if len(txt)>33:
                ws=txt.split(); best=None
                for s in range(1,len(ws)):
                    l1=' '.join(ws[:s]); l2=' '.join(ws[s:]); sc=abs(len(l1)-len(l2))
                    if best is None or sc<best[0]: best=(sc,l1+r'\N'+l2)
                txt=best[1]
            CU.append([a,b,txt])
    CU.sort(); 
    for i in range(len(CU)-1): CU[i][1]=min(CU[i][1],CU[i+1][0]-0.05)
    for a,b,txt in CU: L.append(f"Dialogue: 2,{ts(a)},{ts(b)},Cap,,0,0,0,,{txt}\n")
    L+=extra; return ''.join(L)
def render(name,info,offs,total,ins,fc,lv,la,extra,music_from):
    open(f'build/{name}.ass','w').write(caps(info,offs,extra))
    # music bed from music_raw at a matching point, same processing as the master mix
    ins2=ins+['-ss',f'{music_from:.2f}','-t',f'{total+1:.2f}','-i','/home/claude/ps91m/music_raw.wav']
    m=len(info)
    fc2=fc+[f"[{lv}]trim=duration={total:.3f},setpts=PTS-STARTPTS,vignette=PI/5,ass=build/{name}.ass[v]",
            f"[{la}]highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,volume=2dB[vo]",
            f"[{m}:a]aresample=48000,lowpass=f=2600,aecho=0.8:0.7:90|180|330:0.35|0.25|0.18,aformat=channel_layouts=stereo,volume=-19dB,atrim=duration={total:.3f}[mu]",
            f"[vo][mu]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,atrim=duration={total:.3f}[a]"]
    subprocess.check_call(['ffmpeg','-y','-loglevel','error']+ins2+['-filter_complex',';'.join(fc2),'-map','[v]','-map','[a]','-r','30','-c:v','libx264','-crf','19','-preset','veryfast','-pix_fmt','yuv420p','-video_track_timescale','15360','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',f'build/{name}.mp4'])
    print(name,round(total,2))
if __name__=='__main__':
    what=sys.argv[1]
    if what in ('open','all'):
        info,offs,total,ins,fc,lv,la=build_part('open',OPEN)
        HOOK=[(0.0,1.25,'BEFORE YOU WALK OUT','Hook'),(1.25,2.5,'THAT DOOR TODAY','Hook'),(2.5,3.9,'PRAY THIS FIRST','HookGold')]
        ex=[f"Dialogue: 3,{ts(a)},{ts(b)},{s},,0,0,0,,{{\\fad(60,60)}}{t}\n" for a,b,t,s in HOOK]+[f"Dialogue: 3,{ts(4.4)},{ts(8.2)},HookGold,,0,0,0,,{{\\fad(500,500)\\fs110}}PSALM 91\n"]
        render('open',info,offs,total,ins,fc,lv,la,ex,0.0)
        json.dump({'total':total,'offs':offs,'clips':[(c,st,en) for c,st,en,_,_ in info]},open('build/open.json','w'))
    if what in ('close','all'):
        info,offs,total,ins,fc,lv,la=build_part('close',CLOSE,tail=4.0)
        T=total
        ex=[f"Dialogue: 1,{ts(T-4.6)},{ts(T)},Title,,0,0,0,,{{\\fad(700,900)\\pos(960,840)\\fs100}}TYPE  AMEN\n",f"Dialogue: 1,{ts(T-4.1)},{ts(T)},Sub,,0,0,0,,{{\\fad(700,900)\\pos(960,950)}}BLESSED PRAYERS\n"]
        render('close',info,offs,total,ins,fc,lv,la,ex,ME)
        json.dump({'total':total,'offs':offs,'clips':[(c,st,en) for c,st,en,_,_ in info]},open('build/close.json','w'))
    if what in ('join','all'):
        o=json.load(open('build/open.json'))['total']
        subprocess.check_call(['ffmpeg','-y','-loglevel','error','-ss',f'{MS:.3f}','-to',f'{ME:.3f}','-i',MASTER,'-c:v','libx264','-crf','19','-preset','veryfast','-pix_fmt','yuv420p','-r','30','-video_track_timescale','15360','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-af','afade=t=in:d=0.4,afade=t=out:st=%.3f:d=0.4'%(ME-MS-0.4),'build/mid.mp4'])
        open('build/list.txt','w').write("file 'open.mp4'\nfile 'mid.mp4'\nfile 'close.mp4'\n")
        subprocess.check_call("ffmpeg -y -loglevel error -f concat -safe 0 -i build/list.txt -c copy -movflags +faststart build/Psalm-91-Before-You-Walk-Out-the-Door-NEKO.mp4",shell=True)
        print('joined; mid starts at',round(o,3),'shift',round(o-MS,3))
