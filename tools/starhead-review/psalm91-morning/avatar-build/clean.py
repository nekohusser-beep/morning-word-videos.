# Clean a Seed-VC output: keep the source's exact length, gate silences with the SOURCE speech mask
# (removes the airy hiss/breath Seed-VC leaves in pauses), light spectral denoise, match the source loudness.
import sys, numpy as np, soundfile as sf, subprocess, os
from scipy.signal import resample_poly
from scipy.ndimage import maximum_filter1d, uniform_filter1d
def load(p, sr_out):
    x, sr = sf.read(p, dtype='float32')
    if x.ndim > 1: x = x.mean(1)
    if sr != sr_out:
        from math import gcd; g = gcd(sr, sr_out); x = resample_poly(x, sr_out//g, sr//g).astype(np.float32)
    return x
def mask(src, sr, hop):
    n=len(src)//hop; e=np.sqrt((src[:n*hop].reshape(n,hop)**2).mean(1)+1e-12); db=20*np.log10(e)
    thr=max(np.percentile(db,97)-34,-62); m=(db>thr).astype(np.float32)
    m=maximum_filter1d(m,size=15); m=uniform_filter1d(m,size=3); mm=np.repeat(m,hop)
    mm=np.pad(mm,(0,max(0,len(src)-len(mm))),mode='edge')[:len(src)]
    return uniform_filter1d(mm,size=int(0.012*sr))
def rms(x,m): w=x[m>0.5]; return np.sqrt(np.mean(w**2)+1e-12) if len(w) else 1e-6
def run(src_p, vc_p, out_p, sr=24000):
    src=load(src_p,sr); vc=load(vc_p,sr)
    vc=np.pad(vc,(0,max(0,len(src)-len(vc))))[:len(src)]
    tmp=out_p+'.dn.wav'; sf.write(tmp+'.in.wav',vc,sr)
    subprocess.check_call(['ffmpeg','-y','-loglevel','error','-i',tmp+'.in.wav','-af','highpass=f=75,afftdn=nr=14:nf=-42:tn=1,lowpass=f=10500','-ar',str(sr),'-ac','1',tmp])
    dn=load(tmp,sr); dn=np.pad(dn,(0,max(0,len(src)-len(dn))))[:len(src)]
    m=mask(src,sr,int(sr*0.01)); out=dn*(0.03+0.97*m)
    out*=rms(src,m)/rms(out,m); pk=np.abs(out).max()
    if pk>0.97: out*=0.97/pk
    sf.write(out_p,out.astype(np.float32),sr); os.remove(tmp); os.remove(tmp+'.in.wav')
if __name__=='__main__':
    run(*sys.argv[1:4])
