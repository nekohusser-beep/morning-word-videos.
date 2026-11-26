import subprocess,numpy as np,glob,cv2,sys
final,segdir=sys.argv[1],sys.argv[2]
def aud(p):
    return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',p,'-f','s16le','-ac','1','-ar','8000','-'],capture_output=True).stdout,np.int16).astype(float)
def env(x): 
    n=len(x)//80;return np.sqrt((x[:n*80].reshape(n,80)**2).mean(1))   # 10 ms
F=env(aud(final));t=0;res=[]
for p in sorted(glob.glob(segdir+'/C*.mp4')):
    c=cv2.VideoCapture(p);nf=int(c.get(7));d=nf/30;e=env(aud(p));e=e[20:max(40,min(len(e),int(d*100))-25)];exp=int(round(t*100))+20
    best=max(range(-40,41),key=lambda L:np.corrcoef(e,F[exp+L:exp+L+len(e)])[0,1] if (exp+L>=0 and exp+L+len(e)<=len(F)) else -1)
    res.append((p[-7:-4],best*10));t+=d
print(final,res)
