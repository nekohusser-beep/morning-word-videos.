#!/usr/bin/env python3
"""Per-unit wavs (u000.wav ... in WAVDIR, 24 kHz mono) + units.json -> voice.wav + timings.json.
Gap rules (seconds of silence after a unit): title 3.2 | paragraph end 2.7 | mid-line 0.55 | ends with ':' 0.95 | quote then quote 0.75 |
think-about question 7.5 (a long, quiet pause to actually think) | else 1.25. A think-about question also gets 1.8 s of quiet BEFORE it."""
import json, sys
import numpy as np, soundfile as sf
SP, WAVDIR = sys.argv[1], sys.argv[2]
SR = 24000
units = json.load(open(f"{SP}/units.json"))
def sil(s): return np.zeros(int(SR * s), dtype=np.float32)
parts = [sil(2.0)]; t = 2.0; timings = []
for i, u in enumerate(units):
    a, sr = sf.read(f"{WAVDIR}/u{u['idx']:03d}.wav", dtype="float32")
    assert sr == SR, (u["idx"], sr)
    a = a if a.ndim == 1 else a.mean(axis=1)
    nxt = units[i + 1] if i + 1 < len(units) else None
    if u["kind"] == "think" and not (i > 0 and units[i - 1]["kind"] == "think"):
        pre = 1.8 - 1.25 if not units[i - 1].get("para_end") else 0.0   # previous unit already left its own gap
        if pre > 0: parts.append(sil(pre)); t += pre
    d = len(a) / SR
    timings.append(dict(kind=u["kind"], text=u["text"], t0=round(t, 3), t1=round(t + d, 3)))
    parts.append(a); t += d
    if u["kind"] == "title": gap = 3.2
    elif u["kind"] == "think": gap = 7.5
    elif u.get("para_end"): gap = 2.7
    elif u.get("in_line"): gap = 0.55
    elif u["text"].rstrip().endswith(":"): gap = 0.95
    elif u["kind"] == "quote" and nxt and nxt["kind"] == "quote": gap = 0.75
    else: gap = 1.25
    parts.append(sil(gap)); t += gap
parts.append(sil(5.0)); t += 5.0
voice = np.concatenate(parts)
sf.write(f"{SP}/voice.wav", voice, SR)
json.dump(dict(total=round(t, 3), units=timings), open(f"{SP}/timings.json", "w"), indent=1)
print("units", len(timings), "total seconds", round(t, 1), "minutes", round(t / 60, 2))
