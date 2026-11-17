import sys, os, json, glob
import numpy as np, soundfile as sf, torch
try:
    from speechbrain.inference.speaker import EncoderClassifier
except Exception:
    from speechbrain.pretrained import EncoderClassifier
clf = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="pretrained_ecapa", run_opts={"device": "cpu"})
def load16(p):
    x, sr = sf.read(p, dtype="float32")
    if x.ndim > 1: x = x.mean(1)
    if sr != 16000:
        import torchaudio
        x = torchaudio.functional.resample(torch.from_numpy(x), sr, 16000).numpy()
    return torch.from_numpy(np.ascontiguousarray(x))[None]
def emb(p):
    with torch.no_grad(): e = clf.encode_batch(load16(p)).squeeze()
    return e / e.norm()
cos = lambda a, b: round(float(torch.dot(a, b)), 3)
rawdir, convdir, refdir = sys.argv[1:4]
refs = {k: emb(f"{refdir}/{k}.wav") for k in ("ref1", "ref2")}
out = {"ref2_vs_ref1": cos(refs["ref2"], refs["ref1"]), "raw": {}, "conv": {}}
raw = {os.path.basename(p)[:-4]: emb(p) for p in sorted(glob.glob(f"{rawdir}/src*.wav"))}
for k, e in raw.items(): out["raw"][k] = {"ref1": cos(e, refs["ref1"]), "ref2": cos(e, refs["ref2"])}
rk = list(raw)
M = np.array([[float(torch.dot(raw[a], raw[b])) for b in rk] for a in rk])
out["raw_pairwise_mean"] = round(float(M[np.triu_indices(len(rk), 1)].mean()), 3); out["raw_pairwise_min"] = round(float(M[np.triu_indices(len(rk), 1)].min()), 3)
for tag in sorted({os.path.basename(p).split("_src")[0] for p in glob.glob(f"{convdir}/*_src*.wav")}):
    es = {os.path.basename(p)[:-4].split("_", 1)[1]: emb(p) for p in sorted(glob.glob(f"{convdir}/{tag}_src*.wav"))}
    ks = list(es)
    for k, e in es.items():
        r = {"ref1": cos(e, refs["ref1"]), "ref2": cos(e, refs["ref2"])}
        if k in raw: r["vs_own_raw"] = cos(e, raw[k])
        out["conv"][f"{tag}_{k}"] = r
    M = np.array([[float(torch.dot(es[a], es[b])) for b in ks] for a in ks])
    iu = np.triu_indices(len(ks), 1)
    out["conv"][f"{tag}_pairwise"] = {"mean": round(float(M[iu].mean()), 3), "min": round(float(M[iu].min()), 3)}
print(json.dumps(out, indent=1))
