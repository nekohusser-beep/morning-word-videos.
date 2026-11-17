import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k=Kokoro("../models/kokoro-v1.0.onnx","../models/voices-v1.0.bin")
L=json.load(open('lines.json')); tot=0
for i,l in enumerate(L):
    a,sr=k.create(l,voice='am_michael',speed=1.0,lang='en-us')
    a=np.concatenate([a.astype(np.float32),np.zeros(int(sr*0.25),dtype=np.float32)])
    sf.write(f'a{i:02d}.wav',a,sr); d=len(a)/sr; tot+=d; print(i,round(d,2))
print('total',round(tot,1))
