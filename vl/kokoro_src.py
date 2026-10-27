"""voice-lab source A: Kokoro am_onyx reads each paragraph of vl/lines.txt -> out/K_<n>.wav (24 kHz)."""
import re, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOICE, SPEED = "am_onyx", 0.88
os.makedirs("out", exist_ok=True)
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
paras = [p.strip() for p in open("vl/lines.txt").read().split("\n\n") if p.strip()]
for i, p in enumerate(paras, 1):
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", p) if s.strip()]
    parts, sr = [], 24000
    for j, s in enumerate(sents):
        a, sr = k.create(s, voice=VOICE, speed=SPEED, lang="en-us")
        parts.append(a.astype(np.float32))
        if j < len(sents) - 1:
            parts.append(np.zeros(int(sr * 0.45), dtype=np.float32))
    y = np.concatenate(parts)
    sf.write(f"out/K_{i}.wav", y, sr)
    print(f"K_{i}: {len(y) / sr:.2f}s, {len(p.split())} words", flush=True)
