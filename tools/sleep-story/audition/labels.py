#!/usr/bin/env python3
"""Spoken labels for the audition file: 'Voice one.' ... in a plain narrator voice (not a candidate)."""
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro("../pilot/kokoro-v1.0.onnx", "../pilot/voices-v1.0.bin")
names = ["one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve"]
for i, n in enumerate(names, 1):
    a, sr = k.create(f"Voice {n}.", voice="am_michael", speed=0.95, lang="en-us")
    sf.write(f"lab_{i:02d}.wav", a.astype(np.float32), sr)
a, sr = k.create("Same words every time. Listen to the sound of each voice.", voice="am_michael", speed=0.95, lang="en-us")
sf.write("lab_intro.wav", a.astype(np.float32), sr)
print("labels ok", sr)
