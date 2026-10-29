#!/usr/bin/env python3
"""Assemble ONE labeled audition file: intro, then 'Voice N.' + the same words in each voice. Writes audition.wav, audition.mp3, audition_map.json (start/end seconds per voice)."""
import json, subprocess, sys
import numpy as np, soundfile as sf
SR = 24000
manifest = json.load(open(sys.argv[1]))      # [{"n":1,"id":"Q1","path":"dl/Q1.wav","desc":"..."}...]
def norm(inp, outp):
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",inp,"-af","loudnorm=I=-19:TP=-2:LRA=7,aresample=24000","-ac","1","-ar",str(SR),outp],check=True)
def rd(p):
    a, sr = sf.read(p, dtype="float32"); assert sr == SR, (p, sr)
    return a if a.ndim == 1 else a.mean(axis=1)
def sil(s): return np.zeros(int(SR*s), dtype=np.float32)
parts = [sil(0.5), rd("lab_intro.wav"), sil(1.5)]
t = sum(len(p) for p in parts)/SR
amap = []
for m in manifest:
    norm(m["path"], f"_n_{m['id']}.wav")
    lab, clip = rd(f"lab_{m['n']:02d}.wav"), rd(f"_n_{m['id']}.wav")
    s0 = t
    seq = [lab, sil(0.7), clip, sil(2.2)]
    parts += seq
    t += sum(len(p) for p in seq)/SR
    amap.append(dict(n=m["n"], id=m["id"], start=round(s0,2), clip_start=round(s0+len(lab)/SR+0.7,2), end=round(t-2.2,2), desc=m.get("desc","")))
out = np.concatenate(parts)
sf.write("audition.wav", out, SR)
subprocess.run(["ffmpeg","-y","-loglevel","error","-i","audition.wav","-c:a","libmp3lame","-b:a","160k","audition.mp3"],check=True)
json.dump(amap, open("audition_map.json","w"), indent=1)
print("total", round(len(out)/SR,1), "s;", len(amap), "voices")
for a in amap: print(a["n"], a["id"], a["clip_start"], a["end"])
