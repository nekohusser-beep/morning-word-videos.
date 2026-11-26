"""Little Amens lip-sync retimer. For every clip: measure mouth opening (face landmarks) and voice loudness, pair each
voiced burst with the mouth movement that belongs to it, and build a time map so the picture is retimed to the sound."""
import sys,cv2,numpy as np,subprocess,re,json,os,pickle
E=eval(re.search(r"E=\[(.*?)\]\n",open('build3.py').read(),re.S).group(0)[2:])
SPK={'C01':'L','C07':'L','C11':'R','C14':'L','C18':'L','C19':'L'}          # speaker in two-face clips (left/right); default: the only/biggest face
MAN=json.load(open('v3/anchors_manual.json')) if os.path.exists('v3/anchors_manual.json') else {}
os.makedirs('v3/feat2',exist_ok=True)
def feat(cid):
    fp=f'v3/feat2/{cid}.pkl'
    if os.path.exists(fp): return pickle.load(open(fp,'rb'))
    from fdlite import FaceDetection, FaceDetectionModel, FaceLandmark, face_detection_to_roi
    from PIL import Image
    det=FaceDetection(model_type=FaceDetectionModel.BACK_CAMERA); lm=FaceLandmark()
    p=f'v3/{cid}.mp4';c=cv2.VideoCapture(p);fps=c.get(5)
    raw=subprocess.run(['ffmpeg','-v','error','-i',p,'-af','highpass=f=200,lowpass=f=3500','-f','s16le','-ac','1','-ar','16000','-'],capture_output=True).stdout
    au=np.frombuffer(raw,np.int16).astype(float);hop=16000/fps;rows=[];i=0
    while True:
        ok,f=c.read()
        if not ok:break
        H,W=f.shape[:2];im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));fr=[]
        for d in det(im):
            if d.bbox.width<0.08: continue
            try: L=lm(im,face_detection_to_roi(d,(W,H)))
            except Exception: continue
            if len(L)<300: continue
            fr.append((d.bbox.xmin+d.bbox.width/2,d.bbox.width,abs(L[14].y-L[13].y)*H/(abs(L[291].x-L[61].x)*W+1e-6)))
        rows.append(sorted(fr));i+=1
    e=np.array([np.sqrt((au[int(j*hop):int((j+1)*hop)]**2).mean()+1) if int((j+1)*hop)<=len(au) else 1 for j in range(i)])
    r=dict(fps=fps,n=i,rows=rows,e=e);pickle.dump(r,open(fp,'wb'));return r
def mouth(F,lab):
    n=F['n'];nf=int(np.median([len(r) for r in F['rows'] if r] or [1]));want=SPK.get(lab);xs=[];v=[]
    ref=None
    if nf>=2 and want:
        cx=[ (r[0][0] if want=='L' else r[-1][0]) for r in F['rows'] if len(r)>=2];ref=float(np.median(cx))
    for i,r in enumerate(F['rows']):
        if not r: continue
        if ref is None: f=max(r,key=lambda z:z[1])
        else:
            f=min(r,key=lambda z:abs(z[0]-ref))
            if abs(f[0]-ref)>0.12: continue
        xs.append(i);v.append(f[2])
    m=np.interp(np.arange(n),xs,v);m=np.convolve(np.pad(m,1,mode='edge'),np.ones(3)/3,'valid')
    lo,hi=np.percentile(m,5),np.percentile(m,99);return np.clip((m-lo)/(hi-lo+1e-6),0,1.2),len(xs)/n
def regions(x,thr,gap,minlen):
    R=[];s=None
    for i,v in enumerate(list(x)+[0]):
        if v>thr and s is None: s=i
        if v<=thr and s is not None: R.append([s,i]);s=None
    M=[]
    for r in R:
        if M and r[0]-M[-1][1]<=gap: M[-1][1]=r[1]
        else: M.append(r)
    return [r for r in M if r[1]-r[0]>=minlen]
def anchors(lab,cid):
    F=feat(cid);fps=F['fps'];m,cov=mouth(F,lab);e=F['e']/F['e'].max()
    if lab in MAN: return F,m,e,[tuple(x) for x in MAN[lab]['anchors']],cov
    V=regions(e,0.12,int(0.14*fps),2);Mo=regions(m,0.30,int(0.20*fps),2);A=[];used=set()
    for vs,ve in V:
        best=None
        for j,(ms,me) in enumerate(Mo):
            if j in used: continue
            dlt=(vs-ms)/fps                      # >0: mouth starts before the voice
            if -0.15<=dlt<=0.65 and me>vs-0.05*fps:
                if best is None or abs(dlt-0.1)<abs((vs-Mo[best][0])/fps-0.1): best=j
        if best is None: continue
        used.add(best);ms,me=Mo[best]
        A.append((ms/fps,vs/fps-0.04))
        # end anchor only when this mouth region is not shared with a later burst
        nxt=[v for v in V if v[0]>ve]
        if not nxt or nxt[0][0]>me+0.1*fps: A.append((me/fps,ve/fps+0.05))
    # keep the map monotonic with sane speeds
    A=sorted(set(A));ok=[]
    for v,o in A:
        if ok:
            dv,do=v-ok[-1][0],o-ok[-1][1]
            if dv<=0.04 or do<=0.04 or not (0.45<=dv/do<=2.2): continue
        ok.append((round(v,3),round(o,3)))
    return F,m,e,ok,cov
def vmap(A,a,b,vlen):
    """returns (o0,o1,fn): audio window to use and fn(o)->video time"""
    if not A: return a,b,(lambda o:o)
    A=sorted(A);av=[x[0] for x in A];ao=[x[1] for x in A]
    def fn(o):
        if o<=ao[0]: return av[0]-(ao[0]-o)
        if o>=ao[-1]: return av[-1]+(o-ao[-1])
        return float(np.interp(o,ao,av))
    o0=a
    while fn(o0)<0: o0+=0.01
    o1=b
    while fn(o1)>vlen-0.05: o1-=0.01
    return round(o0,3),round(o1,3),fn
if __name__=='__main__':
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    sel=sys.argv[2:] or [x[0] for x in E];out={}
    fig,ax=plt.subplots(len(sel),2,figsize=(22,2.0*len(sel)),squeeze=False);k=0
    for lab,cid,a,b in E:
        if lab not in sel: continue
        F,m,e,A,cov=anchors(lab,cid);fps=F['fps'];n=F['n'];t=np.arange(n)/fps;a=MAN.get(lab,{}).get('a',a);b=MAN.get(lab,{}).get('b',b);o0,o1,fn=vmap(A,a,b,n/fps)
        out[lab]=dict(cid=cid,anchors=A,o0=o0,o1=o1,cov=round(cov,2))
        for c in (0,1):
            ax[k][c].fill_between(t,0,e,color='orange',alpha=.6)
            if c==0: ax[k][c].plot(t,m,'b-',lw=1.4)
            else:
                oo=np.arange(o0,o1,1/fps);ax[k][c].plot(oo,np.interp([fn(x) for x in oo],t,m),'g-',lw=1.4)
            for v,o in A: ax[k][c].axvline(v if c==0 else o,color='k',alpha=.25,lw=.8)
            ax[k][c].set_xlim(0,8);ax[k][c].set_xticks(np.arange(0,8.01,0.25),minor=True);ax[k][c].grid(True,which='both',alpha=.3);ax[k][c].set_ylabel(lab)
        print(lab,cid,'cov',round(cov,2),'win',o0,o1,'anchors',[(v,o,round(o-v,2)) for v,o in A]);k+=1
    ax[0][0].set_title('BEFORE: mouth opening (blue) vs voice (orange)');ax[0][1].set_title('AFTER retime: mouth opening (green) vs voice (orange)')
    plt.tight_layout();plt.savefig(sys.argv[1],dpi=60)
    old=json.load(open('v3/warp.json')) if os.path.exists('v3/warp.json') else {};old.update(out);json.dump(old,open('v3/warp.json','w'),indent=0)
