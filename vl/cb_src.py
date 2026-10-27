"""voice-lab source B: Chatterbox (MIT) zero-shot clone of vl/ref.wav reads vl/lines.txt -> out/C_<n>.wav."""
import re, os, time, random
import numpy as np, torch, torchaudio as ta

torch.manual_seed(42); np.random.seed(42); random.seed(42)
os.makedirs("out", exist_ok=True)
from chatterbox.tts import ChatterboxTTS

m = ChatterboxTTS.from_pretrained(device="cpu")
paras = [p.strip() for p in open("vl/lines.txt").read().split("\n\n") if p.strip()]
short = torch.zeros(1, int(m.sr * 0.45))
for i, p in enumerate(paras, 1):
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", p) if s.strip()]
    parts = []
    for j, s in enumerate(sents):
        t = time.time()
        w = m.generate(s, audio_prompt_path="vl/ref.wav", exaggeration=0.45, cfg_weight=0.4).cpu()
        parts.append(w)
        if j < len(sents) - 1:
            parts.append(short)
        print(i, j, round(w.shape[-1] / m.sr, 2), "s audio in", round(time.time() - t), "s", flush=True)
    ta.save(f"out/C_{i}.wav", torch.cat(parts, dim=-1), m.sr)
