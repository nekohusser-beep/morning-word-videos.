import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k=Kokoro("/home/claude/models/kokoro-v1.0.onnx","/home/claude/models/voices-v1.0.bin")
for i,l in enumerate(json.load(open('lines.json'))):
    a,sr=k.create(l['say'],voice='am_michael',speed=0.9,lang='en-us')
    a=np.concatenate([a.astype(np.float32),np.zeros(int(sr*0.45),dtype=np.float32)])
    sf.write(f'a{i:02d}.wav',a,sr); print(i,round(len(a)/sr,2))
