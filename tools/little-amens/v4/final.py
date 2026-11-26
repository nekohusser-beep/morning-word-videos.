"""Little Amens EP1 v5 segment renderer: per clip a time map (sound -> picture), a slow push so held poses never read as a frozen frame."""
import sys,cv2,numpy as np,subprocess,re,json,os
import warp
M=warp.MAN
LATE_PLAIN=0.04      # plain clips: sound 40 ms later than Flow's own timing (between the two meters)
LATE_RET=0.09        # retimed clips were measured with sound 50 ms early; same end point
half=lambda A:[(v,round(v+0.5*(o-v)+0.025,3)) for v,o in A]
PLAN={ 'C02':[[1.00,1.06],[2.21,2.58],[2.80,3.08],[3.15,3.92],[4.54,4.80]], 'C03':[[3.40,3.45],[3.96,4.24],[4.92,4.89],[5.05,5.10]], 'C04':M['C04']['anchors'],
       'C05':[(v,o+0.08) for v,o in M['C05']['anchors']], 'C08':half(M['C08']['anchors']),
       'C16':[[0.60,0.55],[1.08,0.88],[1.62,1.70],[2.50,2.50],[2.62,2.64],[3.46,3.62]],
       'C17':[[2.83,2.86],[3.04,3.10],[3.29,3.37],[3.71,3.73],[4.46,4.72],[5.29,5.31],[5.60,5.60]], 'C18':half(M['C18']['anchors']) }
SHIFT={'C02':0.03,'C03':0.03,'C04':0.03,'C05':0.0,'C08':0.03,'C16':0.09,'C17':0.0,'C18':0.03}   # sound later (+) on top of each clip's map
PLAIN=-0.02          # plain clips: sound 20 ms earlier than Flow's own timing (SyncNet 0, Starhead target 0 to 40 ms late)
TRIM={'C01':(0,3.27),'C07':(0.35,3.55),'C08':(0.3,7.9),'C09':(0.6,6.2),'C11':(1.0,5.2),'C12':(3.15,7.2),'C14':(0.1,2.95),'C15':(0.45,7.9),'C19':(0.3,7.0)}
def render(k,lab,cid,a,b,outdir='v3/segG'):
    os.makedirs(outdir,exist_ok=True);a,b=TRIM.get(lab,(a,b));A=[tuple(x) for x in PLAN.get(lab,[])]
    c=cv2.VideoCapture(f'v3/{cid}.mp4');fps=c.get(5);fr=[]
    while True:
        ok,f=c.read()
        if not ok:break
        fr.append(f)
    vlen=len(fr)/fps
    if A:
        _,_,f0=warp.vmap(A,a,b,vlen);fn=lambda o:f0(o+SHIFT[lab])
    else: fn=lambda o:o+PLAIN
    o0=a
    while fn(o0)<0: o0+=0.01
    o1=b
    while fn(o1)>vlen-0.05: o1-=0.01
    dur=o1-o0;n=int(round(dur*30));out=f'{outdir}/{lab}.mp4'
    z0=1.0 if lab=='C17' else 1460/1280;z1=z0+0.035
    if k%2: z0,z1=z1,z0
    y='0' if lab!='C17' else '(ih-ih/zoom)/2'
    vf=f"scale=2560:1440:flags=lanczos,zoompan=z='{z0}+({z1}-{z0})*on/{max(n-1,1)}':d=1:x='(iw-iw/zoom)/2':y='{y}':s=1280x720:fps=30,setsar=1"
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{fr[0].shape[1]}x{fr[0].shape[0]}','-r','30','-i','-',
        '-ss',f'{o0:.3f}','-t',f'{dur:.3f}','-i',f'v3/{cid}.mp4','-map','0:v','-map','1:a','-vf',vf,
        '-af',f'loudnorm=I=-16:TP=-2:LRA=11,afade=t=in:st=0:d=0.06,afade=t=out:st={dur-0.12:.3f}:d=0.12,aresample=48000',
        '-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-video_track_timescale','30000','-t',f'{dur:.3f}',out],stdin=subprocess.PIPE)
    for j in range(n):
        v=fn(o0+j/30);i=min(len(fr)-1,max(0,int(round(v*fps))));p.stdin.write(fr[i].tobytes())
    p.stdin.close();p.wait();return dict(o0=round(o0,3),o1=round(o1,3),dur=round(dur,3),retimed=bool(A))
if __name__=='__main__':
    sel=sys.argv[1:];info=json.load(open('v3/segG/info.json')) if os.path.exists('v3/segG/info.json') else {}
    for k,(lab,cid,a,b) in enumerate(warp.E):
        if sel and lab not in sel: continue
        info[lab]=render(k,lab,cid,a,b);print(lab,info[lab],flush=True)
    json.dump(info,open('v3/segG/info.json','w'))
