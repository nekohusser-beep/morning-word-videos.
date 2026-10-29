#!/usr/bin/env python3
"""Local Kokoro audition candidates + Chatterbox synthetic reference clips. Output: aud/K*.wav, aud/ref_*.wav (24 kHz mono)."""
import json, subprocess, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
SP = "."
SR = 24000
k = Kokoro(f"{SP}/pilot/kokoro-v1.0.onnx", f"{SP}/pilot/voices-v1.0.bin")
segs = json.load(open(f"{SP}/aud/aud_text.json"))["segments"]

def style(name):
    if "+" in name:
        a, b = name.split("+")
        return 0.5 * k.get_voice_style(a) + 0.5 * k.get_voice_style(b)
    return k.get_voice_style(name)

def render(voice, speed=0.82):
    v = style(voice)
    parts = []
    for i, t in enumerate(segs):
        a, sr = k.create(t, voice=v, speed=speed, lang="en-us")
        assert sr == SR
        parts.append(a.astype(np.float32))
        parts.append(np.zeros(int(SR * (1.1 if i < len(segs) - 1 else 0.3)), dtype=np.float32))
    return np.concatenate(parts), np.concatenate(parts[:2])  # full, first segment (hook) for reference

def dsp(inp, outp, pitch):
    # lower the voice a few semitones (pitch scale), warm low end, soften highs, gentle compression, tiny room
    f = (f"rubberband=pitch={pitch}:formant=shifted,bass=g=3.5:f=170,treble=g=-3:f=5500,"
         f"lowpass=f=7600,acompressor=threshold=0.12:ratio=2.5:attack=20:release=300,aecho=0.85:0.7:55:0.15")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", inp, "-af", f, "-ar", str(SR), "-ac", "1", outp], check=True)

jobs = [("K1", "af_heart", None), ("K2", "bf_emma", None),
        ("K3", "af_heart", 0.84), ("K4", "bf_emma", 0.87), ("K5", "af_heart+bf_isabella", 0.86)]
for kid, voice, pitch in jobs:
    full, hook = render(voice)
    sf.write(f"aud/_{kid}_raw.wav", full, SR)
    sf.write(f"aud/_{kid}_hook_raw.wav", hook, SR)
    if pitch:
        dsp(f"aud/_{kid}_raw.wav", f"aud/{kid}.wav", pitch)
        dsp(f"aud/_{kid}_hook_raw.wav", f"aud/ref_{kid}.wav", pitch)
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"aud/_{kid}_raw.wav", "-ar", str(SR), "-ac", "1", f"aud/{kid}.wav"], check=True)
    print(kid, voice, pitch, "ok", round(len(full) / SR, 1), "s", flush=True)
