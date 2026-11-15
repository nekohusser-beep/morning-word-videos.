#!/usr/bin/env python3
"""Score voice-shootout output. usage: score_shootout.py <dir with <engine>_u###.wav>
Baseline = the first take in ep3/final (VoxCPM2 10 steps, cfg 2). Prints per-engine average and lines over the bar."""
import sys, os, glob, json, re, collections, numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
BAR = {"dre": 0.78, "skip": 0.85}
here = os.path.dirname(os.path.abspath(__file__))
enc = VoiceEncoder()
ref = {w: enc.embed_utterance(preprocess_wav(f"{here}/lock/ref_{w}.wav")) for w in BAR}
kind = {}
for w in BAR:
    for u in json.load(open(f"{here}/shootout/{w}.json")):
        kind[u["idx"]] = w
def score(p, idx):
    return float(np.dot(enc.embed_utterance(preprocess_wav(p)), ref[kind[idx]]))
res = collections.defaultdict(dict)
for idx in kind:
    p = f"{here}/ep3/final/u{idx:03d}.wav"
    if os.path.exists(p):
        res["baseline_t10_c2"][idx] = score(p, idx)
for p in glob.glob(f"{sys.argv[1]}/*_u*.wav"):
    m = re.match(r"(.+)_u(\d{3})\.wav", os.path.basename(p))
    if m and int(m.group(2)) in kind:
        res[m.group(1)][int(m.group(2))] = score(p, int(m.group(2)))
for eng, d in sorted(res.items(), key=lambda kv: -np.mean(list(kv[1].values()))):
    ok = sum(v >= BAR[kind[i]] for i, v in d.items())
    dre = [v for i, v in d.items() if kind[i] == "dre"]; sk = [v for i, v in d.items() if kind[i] == "skip"]
    print(f"{eng:18s} lines {len(d):2d}  avg {np.mean(list(d.values())):.3f}  dre {np.mean(dre) if dre else 0:.3f}  skip {np.mean(sk) if sk else 0:.3f}  over bar {ok}/{len(d)}")
