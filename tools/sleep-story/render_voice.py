#!/usr/bin/env python3
"""Render the pilot narration with Kokoro af_sarah (free, local). Writes voice.wav + timings.json.
Script format: 'T: ' title, plain lines narration, '» ' lines KJV quote, blank = paragraph break."""
import json, re, sys
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

SP = sys.argv[1]
SR = 24000
VOICE, SPEED = "af_sarah", 0.82
k = Kokoro(f"{SP}/pilot/kokoro-v1.0.onnx", f"{SP}/pilot/voices-v1.0.bin")


def sil(s):
    return np.zeros(int(SR * s), dtype=np.float32)


def spoken(s):
    s = s.replace("’", "'")
    s = s.replace("LORD", "Lord")
    s = re.sub(r"\bfourscore\b", "four score", s)
    return s


def say(t):
    a, sr = k.create(spoken(t), voice=VOICE, speed=SPEED, lang="en-us")
    assert sr == SR
    return a.astype(np.float32)


# parse into units
lines = [l.rstrip("\n") for l in open(f"{SP}/script.txt", encoding="utf-8")]
units = []   # dict(kind, text, line_end(bool), para_end(bool), cont(bool))
for i, l in enumerate(lines):
    if not l.strip():
        if units:
            units[-1]["para_end"] = True
        continue
    if l.startswith("T: "):
        units.append(dict(kind="title", text=l[3:].strip(), para_end=False))
    elif l.startswith("» "):
        units.append(dict(kind="quote", text=l[2:].strip(), para_end=False))
    else:
        sents = re.split(r"(?<=[.!?])\s+(?=[A-Z])", l.strip())
        for j, s in enumerate(sents):
            units.append(dict(kind="narr", text=s, para_end=False, in_line=(j < len(sents) - 1)))
        # next unit marks line end implicitly

parts = [sil(2.0)]
t = 2.0
timings = []
for idx, u in enumerate(units):
    a = say(u["text"])
    d = len(a) / SR
    timings.append(dict(kind=u["kind"], text=u["text"], t0=round(t, 3), t1=round(t + d, 3)))
    parts.append(a)
    t += d
    nxt = units[idx + 1] if idx + 1 < len(units) else None
    if u["kind"] == "title":
        gap = 3.2
    elif u.get("para_end"):
        gap = 2.7
    elif u.get("in_line"):
        gap = 0.55
    elif u["text"].rstrip().endswith(":"):
        gap = 0.95
    elif u["kind"] == "quote" and nxt and nxt["kind"] == "quote":
        gap = 0.75
    else:
        gap = 1.25
    parts.append(sil(gap))
    t += gap
parts.append(sil(5.0))
t += 5.0
voice = np.concatenate(parts)
sf.write(f"{SP}/voice.wav", voice, SR)
json.dump(dict(total=round(t, 3), units=timings), open(f"{SP}/timings.json", "w"), indent=1)
print("units", len(timings), "total seconds", round(t, 1), "minutes", round(t / 60, 2))
