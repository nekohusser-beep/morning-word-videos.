import json, os, numpy as np, soundfile as sf
GAP = 1.0
def segs():
    return json.load(open(os.environ.get("TEXT_JSON","tools/verse-voice/text.json")))["segments"]
def join(chunks, sr, out):
    parts = []
    for i, c in enumerate(chunks):
        parts.append(np.asarray(c, dtype=np.float32).reshape(-1))
        parts.append(np.zeros(int(sr * (GAP if i < len(chunks) - 1 else 0.4)), dtype=np.float32))
    a = np.concatenate(parts)
    pk = float(np.abs(a).max()) or 1.0
    if pk > 0.97:
        a = a * (0.97 / pk)
    sf.write(out, a, sr)
    print("wrote", out, round(len(a) / sr, 1), "s @", sr, flush=True)
