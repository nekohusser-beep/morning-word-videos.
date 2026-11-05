"""Chatterbox (MIT): built-in default voice, or a clone of a SYNTHETIC reference (a Kokoro voice, deepened). CPU."""
import os, re, sys, time, random
sys.path.insert(0, "tools/sleep-story/audition")
import numpy as np, torch
from common import segs, join
torch.manual_seed(42); np.random.seed(42); random.seed(42)
ID, REF = sys.argv[1], sys.argv[2]
from chatterbox.tts import ChatterboxTTS
m = ChatterboxTTS.from_pretrained(device="cpu")
kw = {} if REF == "default" else {"audio_prompt_path": REF}
chunks = []
for pi, p in enumerate(segs()):
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", p) if x.strip()]
    parts = []
    for si, s in enumerate(sents):
        t0 = time.time()
        w = m.generate(s, exaggeration=0.4, cfg_weight=0.4, **kw).cpu().numpy().reshape(-1)
        parts.append(w)
        if si < len(sents) - 1:
            parts.append(np.zeros(int(m.sr * 0.35), dtype=np.float32))
        print(pi, si, round(len(w) / m.sr, 1), "s in", round(time.time() - t0), "s", flush=True)
    chunks.append(np.concatenate(parts))
os.makedirs("out", exist_ok=True)
join(chunks, m.sr, f"out/C_{ID}.wav")
