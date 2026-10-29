import json, sys, re
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
SP = sys.argv[1]
SR = 24000
k = Kokoro(f"{SP}/pilot/kokoro-v1.0.onnx", f"{SP}/pilot/voices-v1.0.bin")
d = json.load(open(f"{SP}/timings.json"))
v, sr = sf.read(f"{SP}/voice.wav", dtype="float32")
assert sr == SR
us = d["units"]
i = next(n for n, u in enumerate(us) if u["text"].startswith("Wherefore he is able also to save them"))
u, nx = us[i], us[i + 1]
txt = u["text"].replace("’", "'").replace("LORD", "Lord").replace("fourscore", "four score").replace("liveth", "livith")
a, _ = k.create(txt, voice="af_sarah", speed=0.82, lang="en-us")
a = a.astype(np.float32)
s0, s1 = int(round(u["t0"] * SR)), int(round(nx["t0"] * SR))
slot = s1 - s0
old_len = int(round((u["t1"] - u["t0"]) * SR))
print("old dur", round(old_len / SR, 2), "new dur", round(len(a) / SR, 2), "gap left", round((slot - len(a)) / SR, 2))
assert slot - len(a) > int(0.4 * SR), "no room"
seg = np.concatenate([a, np.zeros(slot - len(a), dtype=np.float32)])
out = v.copy()
out[s0:s1] = seg
sf.write(f"{SP}/voice2.wav", out, SR)
print("wrote voice2.wav", len(out) / SR, "s (original", len(v) / SR, ")")
