#!/usr/bin/env python3
"""Render script units with Chatterbox (MIT), CPU. Same settings as the audition (exaggeration 0.4, cfg 0.4).
usage: eng_units_chatterbox.py UNITS_JSON REF|default CHUNK N_CHUNKS OUTDIR   -> OUTDIR/uNNN.wav (24 kHz mono), units where idx % N_CHUNKS == CHUNK"""
import json, os, random, re, sys, time
import numpy as np, soundfile as sf, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spoken import spoken
torch.manual_seed(42); np.random.seed(42); random.seed(42)
units_path, ref, chunk, n, outdir = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
os.makedirs(outdir, exist_ok=True)
units = json.load(open(units_path))
from chatterbox.tts import ChatterboxTTS
m = ChatterboxTTS.from_pretrained(device="cpu")
kw = {} if ref == "default" else {"audio_prompt_path": ref}
for u in units:
    if u["idx"] % n != chunk:
        continue
    t0 = time.time()
    w = m.generate(spoken(u["text"]), exaggeration=0.4, cfg_weight=0.4, **kw).cpu().numpy().reshape(-1).astype(np.float32)
    sf.write(f"{outdir}/u{u['idx']:03d}.wav", w, m.sr)
    print(u["idx"], u["kind"], round(len(w) / m.sr, 1), "s in", round(time.time() - t0), "s :", u["text"][:50], flush=True)
