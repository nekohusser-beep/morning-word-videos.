import json, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k=Kokoro("models/kokoro-v1.0.onnx","models/voices-v1.0.bin")
L=json.load(open('lines.json'))
only=sys.argv[1:] 
for l in L:
    if only and l['id'] not in only: continue
    a,sr=k.create(l['say'],voice='am_michael',speed=float(l.get('speed',1.0)),lang='en-us')
    sf.write(f"vo_{l['id']}.wav",a.astype(np.float32),sr); print(l['id'],round(len(a)/sr,2),sr)
