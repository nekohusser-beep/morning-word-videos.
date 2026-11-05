#!/usr/bin/env python3
"""Objective voice numbers: median F0, pitch movement (10-90 percentile range in semitones), voiced share, speech rate proxy."""
import sys, numpy as np, soundfile as sf, parselmouth
def stats(path, t0=None, t1=None):
    a, sr = sf.read(path, dtype="float64")
    if a.ndim > 1: a = a.mean(axis=1)
    if t0 is not None: a = a[int(t0 * sr): int((t1 or len(a) / sr) * sr)]
    snd = parselmouth.Sound(a, sampling_frequency=sr)
    pit = snd.to_pitch(time_step=0.01, pitch_floor=60, pitch_ceiling=400)
    f = pit.selected_array["frequency"]; f = f[f > 0]
    if len(f) < 20: return None
    st = 12 * np.log2(f / np.median(f))
    dur = len(a) / sr
    return dict(f0_median=round(float(np.median(f))), pitch_range_st=round(float(np.percentile(st, 90) - np.percentile(st, 10)), 1),
                voiced_pct=round(100 * len(f) * 0.01 / dur), dur=round(dur, 1))
if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p, stats(p))
