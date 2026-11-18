#!/usr/bin/env python3
"""Pick the best take per line by voice match. usage: pick_takes.py <ep_dir> <take_dir> [<take_dir> ...]
Scores <ep_dir>/final/u###.wav and each <take_dir>/u###.wav against lock/ref_<who>.wav (resemblyzer),
copies the best into <ep_dir>/final, prints the table and the lines still under the bar (dre 0.78, skip 0.85)."""
import sys, os, json, shutil, numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
BAR = {"dre": 0.78, "skip": 0.85, "nia": 0.85}
here = os.path.dirname(os.path.abspath(__file__))
ep, takes = sys.argv[1], sys.argv[2:]
enc = VoiceEncoder()
ref = {w: enc.embed_utterance(preprocess_wav(f"{here}/lock/ref_{w}.wav")) for w in BAR}
under = []
for l in json.load(open(f"{ep}/lines.json")):
    name = f"u{l['idx']:03d}.wav"
    cands = [f"{ep}/final/{name}"] + [f"{t}/{name}" for t in takes if os.path.exists(f"{t}/{name}")]
    sc = [(float(np.dot(enc.embed_utterance(preprocess_wav(c)), ref[l["kind"]])), c) for c in cands]
    best = max(sc)
    if best[1] != cands[0]:
        shutil.copy(best[1], cands[0])
    ok = best[0] >= BAR[l["kind"]]
    if not ok:
        under.append(l["idx"])
    print(f"{name} {l['kind']:4s} {best[0]:.3f} {'PASS' if ok else 'under'} from {os.path.basename(os.path.dirname(best[1]))}  {l['text'][:44]}")
print("UNDER BAR:", under)
