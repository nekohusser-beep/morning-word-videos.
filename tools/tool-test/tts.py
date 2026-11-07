import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k=Kokoro("models/kokoro-v1.0.onnx","models/voices-v1.0.bin")
L=json.load(open('lines.json'))
for i,l in enumerate(L):
    a,sr=k.create(l['say'],voice='am_michael',speed=1.08,lang='en-us')
    pad=np.zeros(int(sr*0.18),dtype=np.float32)
    a=np.concatenate([a.astype(np.float32),pad])
    sf.write(f'a{i:02d}.wav',a,sr); print(i,round(len(a)/sr,2))
