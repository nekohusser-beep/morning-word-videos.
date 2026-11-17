#!/usr/bin/env python3
"""voice.wav + a soft generated ambient pad (sines, no samples, no license issue) -> mix.wav (stereo, 24 kHz)."""
import sys
import numpy as np
import soundfile as sf

SP = sys.argv[1]
v, sr = sf.read(f"{SP}/voice.wav", dtype="float32")
n = len(v)
t = np.arange(n, dtype=np.float64) / sr
dur = n / sr

# voice speech level (RMS of the loud parts only)
win = sr // 2
fr = v[: n - n % win].reshape(-1, win)
rms = np.sqrt((fr ** 2).mean(axis=1))
speech_rms = float(np.sqrt((rms[rms > 0.01] ** 2).mean()))


def pad(chan):
    rng = np.random.default_rng(40 + chan)
    out = np.zeros(n, dtype=np.float64)
    notes = [(55.0, 0.55), (110.0, 0.9), (164.81, 0.7), (220.0, 0.8), (246.94, 0.30), (329.63, 0.38), (440.0, 0.12)]
    for f, a in notes:
        for det in (-0.22, 0.0, 0.19):
            ph = rng.random() * 6.283
            lfo_f = rng.uniform(0.018, 0.045)
            lfo_p = rng.random() * 6.283
            amp = a * (0.55 + 0.45 * np.sin(2 * np.pi * lfo_f * t + lfo_p))
            out += amp * np.sin(2 * np.pi * (f + det + 0.07 * chan) * t + ph) / 3.0
    return out


L, R = pad(0), pad(1)
pr = float(np.sqrt((L ** 2).mean()))
target = speech_rms * 10 ** (-25.0 / 20)      # pad sits about 25 dB under the voice
g = target / pr
L, R = (L * g).astype(np.float32), (R * g).astype(np.float32)
# pad fades in over 6 s, out over the last 10 s
env = np.ones(n, dtype=np.float32)
fi, fo = int(6 * sr), int(10 * sr)
env[:fi] = np.linspace(0, 1, fi)
env[-fo:] = np.linspace(1, 0, fo)
L *= env
R *= env
mix = np.stack([v + L, v + R], axis=1)
peak = float(np.abs(mix).max())
if peak > 0.95:
    mix *= 0.95 / peak
sf.write(f"{SP}/mix.wav", mix, sr)
print("duration", round(dur, 1), "speech_rms", round(speech_rms, 4), "pad_rms", round(target, 5), "peak", round(float(np.abs(mix).max()), 3))
