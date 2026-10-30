"""VoxCPM2 (Apache 2.0): voice design from a short description in parentheses before the text. CPU."""
import os, sys, time, inspect, traceback
sys.path.insert(0, "tools/verse-voice")
import numpy as np
from common import segs, join
ID, DESC = sys.argv[1], os.environ["DESC"]
from voxcpm import VoxCPM
print("generate", inspect.signature(VoxCPM.generate), flush=True)
model = None
for mid in ("openbmb/VoxCPM2", "openbmb/VoxCPM2-2B"):
    try:
        model = VoxCPM.from_pretrained(mid)
        print("loaded", mid, flush=True)
        break
    except Exception:
        traceback.print_exc()
assert model is not None, "model did not load"
sr = getattr(getattr(model, "tts_model", model), "sample_rate", 48000)
chunks = []
for i, t in enumerate(segs()):
    t0 = time.time()
    w = None
    for kw in ({"cfg_value": 2.0, "inference_timesteps": 10}, {}):
        try:
            w = model.generate(text=f"({DESC}){t}", **kw)
            break
        except Exception:
            traceback.print_exc()
    assert w is not None, "generate failed"
    w = np.asarray(w, dtype=np.float32).reshape(-1)
    chunks.append(w)
    print("seg", i, round(len(w) / sr, 1), "s audio in", round(time.time() - t0), "s", flush=True)
os.makedirs("out", exist_ok=True)
join(chunks, int(sr), f"out/{ID}.wav")
