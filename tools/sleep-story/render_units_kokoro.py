#!/usr/bin/env python3
"""Render script units with Kokoro locally, optional DSP (lower + warm). usage: render_units_kokoro.py SP VOICE[+VOICE2] PITCH|none OUTDIR
Same chain as the audition (rubberband pitch, bass shelf, soft highs, light compression and room) so the voice matches what Neko heard."""
import json, subprocess, sys, os
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
SP, voice, pitch, outdir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, SP)
from spoken import spoken
os.makedirs(outdir, exist_ok=True)
k = Kokoro(f"{SP}/pilot/kokoro-v1.0.onnx", f"{SP}/pilot/voices-v1.0.bin")
if "+" in voice:
    a, b = voice.split("+"); style = 0.5 * k.get_voice_style(a) + 0.5 * k.get_voice_style(b)
else:
    style = k.get_voice_style(voice)
units = json.load(open(f"{SP}/units.json"))
for u in units:
    a, sr = k.create(spoken(u["text"], "kokoro"), voice=style, speed=0.82, lang="en-us")
    raw = f"{outdir}/_raw{u['idx']:03d}.wav"; out = f"{outdir}/u{u['idx']:03d}.wav"
    sf.write(raw, a.astype(np.float32), sr)
    if pitch != "none":
        f = (f"rubberband=pitch={pitch}:formant=shifted,bass=g=3.5:f=170,treble=g=-3:f=5500,lowpass=f=7600,"
             "acompressor=threshold=0.12:ratio=2.5:attack=20:release=300,aecho=0.85:0.7:55:0.15")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", f, "-ar", "24000", "-ac", "1", out], check=True)
        os.remove(raw)
    else:
        os.replace(raw, out)
    print(u["idx"], flush=True)
