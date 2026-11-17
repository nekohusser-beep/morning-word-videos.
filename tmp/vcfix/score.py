import sys, os, json, glob
import numpy as np, soundfile as sf, torch
try:
    from speechbrain.inference.speaker import EncoderClassifier
except Exception:
    from speechbrain.pretrained import EncoderClassifier
clf = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="pretrained_ecapa", run_opts={"device": "cpu"})

def load16(p, a=None, b=None):
    x, sr = sf.read(p, dtype="float32")
    if x.ndim > 1: x = x.mean(1)
    if sr != 16000:
        import torchaudio
        x = torchaudio.functional.resample(torch.from_numpy(x), sr, 16000).numpy(); sr = 16000
    if a is not None: x = x[int(a * sr):int(b * sr)]
    return torch.from_numpy(np.ascontiguousarray(x))[None]

def emb(p, a=None, b=None):
    with torch.no_grad(): e = clf.encode_batch(load16(p, a, b)).squeeze()
    return e / e.norm()

cdir, bdir = sys.argv[1:3]
refs = {k: emb(f"{bdir}/{k}.wav") for k in ("ref1", "ref2")}
cos = lambda a, b: round(float(torch.dot(a, b)), 3)
# word windows (seconds) inside each 22.05k segment
WIN = {"seg1": (0.30, 1.29), "seg2": (0.30, 1.215), "orig1": (0.305, 0.825), "orig2": (0.30, 0.855)}
out = {"yardstick": {}, "items": {}}
# yardstick: how close are Derrick's OWN 1.1 s windows (ref2) to ref1, and ref2 whole to ref1
w = []
for t in np.arange(0, 12.5, 1.0):
    w.append(cos(emb(f"{bdir}/ref2.wav", t, t + 1.1), refs["ref1"]))
out["yardstick"] = {"ref2_whole_vs_ref1": cos(refs["ref2"], refs["ref1"]), "ref2_1.1s_windows_vs_ref1": {"min": min(w), "mean": round(float(np.mean(w)), 3), "max": max(w)}}
items = {"RAW_" + k: f"{bdir}/{k}.wav" for k in ("seg1", "seg2")}
items.update({"DERRICK_" + k: f"{bdir}/{k}.wav" for k in ("orig1", "orig2")})
for p in sorted(glob.glob(f"{cdir}/vcfix_*.wav")):
    n = os.path.basename(p)[:-4].split("_", 2)[2]   # e.g. A_seg1
    items["VC_" + n] = p
for name, p in items.items():
    seg = name.split("_")[-1]
    a, b = WIN.get(seg, (0, None))
    d = {"whole_vs_ref1": cos(emb(p), refs["ref1"]), "whole_vs_ref2": cos(emb(p), refs["ref2"])}
    if b: d["word_vs_ref1"] = cos(emb(p, a, b), refs["ref1"]); d["word_vs_ref2"] = cos(emb(p, a, b), refs["ref2"])
    out["items"][name] = d
print(json.dumps(out, indent=1))
