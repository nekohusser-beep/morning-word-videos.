"""Render one retimed segment per clip. variant A = plain clip with the constant SyncNet correction (audio 0.08 s earlier);
variant B = per-word retime from v3/anchors_manual.json."""
import sys,cv2,numpy as np,subprocess,re,json,os
import warp
MAN=warp.MAN; G=0.05
def render(lab,cid,a,b,variant,outdir):
    os.makedirs(outdir,exist_ok=True);m=MAN.get(lab,{});a=m.get('a',a);b=m.get('b',b)
    A=[tuple(x) for x in m.get('anchors',[])] if variant in 'BCE' else []
    if variant=='C': A=[(v,o+G) for v,o in A]
    if variant=='D': A=[(v,round(v+0.5*(o-v)+G/2,3)) for v,o in m.get('anchors',[])]
    if not A: A=[(0.0,G)]
    c=cv2.VideoCapture(f'v3/{cid}.mp4');fps=c.get(5);fr=[]
    while True:
        ok,f=c.read()
        if not ok:break
        fr.append(f)
    o0,o1,fn=warp.vmap(A,a,b,len(fr)/fps);o0=max(o0,a);dur=o1-o0;n=int(round(dur*30));out=f'{outdir}/{lab}.mp4'
    vf='scale=1280:720,setsar=1' if lab=='C17' else 'scale=1460:822,crop=1280:720:90:0,setsar=1'
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{fr[0].shape[1]}x{fr[0].shape[0]}','-r','30','-i','-',
        '-ss',f'{o0:.3f}','-t',f'{dur:.3f}','-i',f'v3/{cid}.mp4','-map','0:v','-map','1:a','-vf',vf,
        '-af',f'loudnorm=I=-16:TP=-2:LRA=11,afade=t=in:st=0:d=0.06,afade=t=out:st={dur-0.12:.3f}:d=0.12,aresample=48000',
        '-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-video_track_timescale','30000','-t',f'{dur:.3f}',out],stdin=subprocess.PIPE)
    for j in range(n):
        v=fn(o0+j/30);i=min(len(fr)-1,max(0,int(round(v*fps))));p.stdin.write(fr[i].tobytes())
    p.stdin.close();p.wait();return dict(o0=round(o0,3),o1=round(o1,3),dur=round(dur,3))
if __name__=='__main__':
    variant=sys.argv[1];sel=sys.argv[2:];info={}
    for lab,cid,a,b in warp.E:
        if sel and lab not in sel: continue
        if variant in 'BCDE' and not MAN.get(lab,{}).get('anchors'): continue
        info[lab]=render(lab,cid,a,b,variant,f'v3/seg{variant}');print(variant,lab,info[lab],flush=True)
    json.dump(info,open(f'v3/seg{variant}/info.json','w'))
