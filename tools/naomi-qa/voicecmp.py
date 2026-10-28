import sys, subprocess, numpy as np
def pcm(f, sr=16000):
    raw=subprocess.run(['ffmpeg','-v','error','-i',f,'-ac','1','-ar',str(sr),'-f','f32le','-'],capture_output=True).stdout
    return np.frombuffer(raw,dtype=np.float32)
def feats(a, sr=16000, n=1024, hop=512):
    win=np.hanning(n); fr=[]
    thr=max(np.sqrt(np.mean(a**2))*0.8,0.01)
    for i in range(0,len(a)-n,hop):
        x=a[i:i+n]
        if np.sqrt(np.mean(x**2))<thr: continue
        fr.append(np.abs(np.fft.rfft(x*win))**2)
    S=np.mean(fr,axis=0); freqs=np.fft.rfftfreq(n,1/sr)
    edges=np.geomspace(100,7500,28)
    ltas=np.array([10*np.log10(S[(freqs>=edges[k])&(freqs<edges[k+1])].sum()+1e-12) for k in range(27)])
    ltas-=ltas.mean()
    cen=float((freqs*S).sum()/S.sum())
    return ltas,cen,len(fr)
fs=sys.argv[1:]
F=[feats(pcm(f)) for f in fs]
for f,(l,c,n) in zip(fs,F): print('%-28s centroid %.0f Hz  voiced frames %d'%(f.split('/')[-1],c,n))
print('LTAS correlation / RMS band diff (dB):')
for i in range(len(fs)):
    for j in range(i+1,len(fs)):
        a,b=F[i][0],F[j][0]
        print('  %s vs %s: r=%.3f  rmsdiff=%.2f dB'%(fs[i].split('/')[-1],fs[j].split('/')[-1],np.corrcoef(a,b)[0,1],np.sqrt(np.mean((a-b)**2))))
