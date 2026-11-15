"""Voice-match gate for Skip episodes (Nov 12 2026). Usage: python voice_gate.py <lines.json> <wav_dir>
Scores each u###.wav against tools/skip-voice/lock/ref_<who>.wav with resemblyzer. Bar from approved Ep1: dre 0.78, skip 0.85.
Never pitch-shift a line to pass; re-voice it."""
import sys, os, json, numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
BAR = {"dre": 0.78, "skip": 0.85}
here = os.path.dirname(os.path.abspath(__file__))
enc = VoiceEncoder()
ref = {w: enc.embed_utterance(preprocess_wav(f"{here}/lock/ref_{w}.wav")) for w in BAR}
bad = 0
for l in json.load(open(sys.argv[1])):
    f = f"{sys.argv[2]}/u{l['idx']:03d}.wav"
    s = float(np.dot(enc.embed_utterance(preprocess_wav(f)), ref[l["kind"]]))
    ok = s >= BAR[l["kind"]]; bad += not ok
    print(f"u{l['idx']:03d} {l['kind']:4s} {s:.3f} {'PASS' if ok else 'FAIL'}  {l['text'][:50]}")
print("FAILS:", bad); sys.exit(1 if bad else 0)
