import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k=Kokoro("/tmp/nw/kokoro-v1.0.onnx","/tmp/nw/voices-v1.0.bin")
L=[
"If you're awake right now while the rest of the street is asleep, this one's for you.",
"My soul waiteth for the Lord more than they that watch for the morning:",
"I say, more than they that watch for the morning.",
"That's Psalm one hundred thirty, verse six.",
"A night watchman stood on the wall for hours, and the only thing he wanted was daylight.",
"I've worked enough overnights to know that wait, with the clock crawling toward morning.",
"The writer says he waits on God harder than that watchman waits on the sun.",
"And the sun always came up. Every night that watchman ever stood, the morning showed up.",
"Father, for everybody still up tonight, at work, at a bedside, or just wide awake, be near them.",
"In Jesus' name, amen.",
"Morning's coming. Follow so the Word finds you on the long nights. Have a blessed day.",
]
out=[]
for i,t in enumerate(L,1):
    a,sr=k.create(t,voice='am_michael',speed=0.94,lang='en-us')
    a=a.astype(np.float32)
    sf.write(f'l{i:02d}.wav',a,sr); out.append({"n":i,"text":t,"dur":round(len(a)/sr,3)}); print(i,round(len(a)/sr,2),round(len(t.split())/(len(a)/sr),2),'w/s',flush=True)
json.dump(out,open('tl.json','w'),indent=1); print(sr)
