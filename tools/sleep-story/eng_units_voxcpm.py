#!/usr/bin/env python3
"""Render script units with VoxCPM2 (Apache 2.0), CPU, in ONE locked voice: the reference clip is the exact audition sample Neko picked (Voice 4).
usage: eng_units_voxcpm.py UNITS_JSON REF_WAV REF_TEXT_FILE CHUNK N_CHUNKS OUTDIR  -> OUTDIR/uNNN.wav (native sample rate), units where idx % N_CHUNKS == CHUNK"""
import inspect, json, os, random, sys, time, traceback
import numpy as np, soundfile as sf, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spoken import spoken
units_path, ref, ref_text_path, chunk, n, outdir = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
os.makedirs(outdir, exist_ok=True)
ref_text = open(ref_text_path, encoding="utf-8").read().strip()
units = [u for u in json.load(open(units_path)) if u["idx"] % n == chunk]
from voxcpm import VoxCPM
src = ""
for obj in (VoxCPM,):
    try:
        src += inspect.getsource(obj)
    except Exception:
        traceback.print_exc()
try:
    import voxcpm.model as vm
    src += inspect.getsource(vm)
except Exception:
    pass
keys = ["prompt_wav_path", "prompt_text", "reference_wav_path", "cfg_value", "inference_timesteps", "denoise", "normalize"]
print("source mentions:", [k for k in keys if k in src], flush=True)
model = VoxCPM.from_pretrained("openbmb/VoxCPM2")
sr = int(getattr(getattr(model, "tts_model", model), "sample_rate", 48000))
base = {"cfg_value": 2.0, "inference_timesteps": 10}
modes = [("prompt+text", {"prompt_wav_path": ref, "prompt_text": ref_text, **base}),
         ("reference", {"reference_wav_path": ref, **base})]
modes = [(nm, kw) for nm, kw in modes if (not src) or all(k in src for k in kw)] or modes
print("modes to try:", [m[0] for m in modes], flush=True)
chosen = None
for u in units:
    text = spoken(u["text"])
    words = max(1, len(text.split()))
    w = None
    for attempt in range(3):
        torch.manual_seed(1000 + u["idx"] * 7 + attempt); np.random.seed(1000 + u["idx"]); random.seed(1000 + u["idx"])
        for nm, kw in ([chosen] if chosen else modes):
            t0 = time.time()
            try:
                x = np.asarray(model.generate(text=text, **kw), dtype=np.float32).reshape(-1)
            except Exception:
                traceback.print_exc(); continue
            d = len(x) / sr
            ok = 0.20 * words <= d <= 1.6 * words + 1.5
            print(u["idx"], u["kind"], nm, "attempt", attempt, round(d, 1), "s in", round(time.time() - t0), "s ok" if ok else "BAD LENGTH", ":", text[:46], flush=True)
            if ok:
                w, chosen = x, (nm, kw); break
        if w is not None:
            break
    if w is None:
        print("GAVE UP on unit", u["idx"], flush=True)
        continue
    sf.write(f"{outdir}/u{u['idx']:03d}.wav", w, sr)
print("done chunk", chunk, "mode", chosen[0] if chosen else None, flush=True)
