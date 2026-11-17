import sys,json,re,soundfile as sf,numpy as np
from kokoro_onnx import Kokoro
k=Kokoro("kokoro-v1.0.onnx","voices-v1.0.bin")
mode=sys.argv[1]
if mode=="test":
    for v in ["am_michael","am_onyx","am_adam"]:
        a,sr=k.create("Before your feet hit the floor this morning, the math had already started.",voice=v,speed=1.0,lang="en-us")
        sf.write(f"t_{v}.wav",a,sr); print(v,len(a)/sr)
else:
    lines=json.load(open(sys.argv[2])); out=sys.argv[3]; sp=float(sys.argv[4]) if len(sys.argv)>4 else 1.0
    import os; os.makedirs(out,exist_ok=True)
    for L in lines:
        parts=[x.strip() for x in re.split(r'(?<=[.!?:])\s+', L["text"]) if x.strip()]
        for i,p in enumerate(parts):
            a,sr=k.create(p,voice="am_michael",speed=sp,lang="en-us"); sf.write(f"{out}/{L['name']}_s{i:02d}.wav",a,sr)
        print(L["name"],len(parts))
