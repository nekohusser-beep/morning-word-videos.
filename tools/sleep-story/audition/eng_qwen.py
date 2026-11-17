"""Qwen3-TTS VoiceDesign (Apache 2.0): a voice made from a text description of the SOUND. CPU, fp32."""
import os, sys, time, inspect, traceback
sys.path.insert(0, "tools/sleep-story/audition")
import numpy as np, torch
from common import segs, join
ID, INSTRUCT = sys.argv[1], os.environ["INSTRUCT"]
from qwen_tts import Qwen3TTSModel
print("from_pretrained", inspect.signature(Qwen3TTSModel.from_pretrained), flush=True)
print("generate_voice_design", inspect.signature(Qwen3TTSModel.generate_voice_design), flush=True)
MID = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
model = None
for kw in ({"device_map": "cpu", "dtype": torch.float32}, {"device_map": "cpu", "torch_dtype": torch.float32}, {}):
    try:
        model = Qwen3TTSModel.from_pretrained(MID, **kw)
        print("loaded with", kw, flush=True)
        break
    except Exception:
        traceback.print_exc()
assert model is not None, "model did not load"
chunks, sr_out = [], None
for i, t in enumerate(segs()):
    t0 = time.time()
    wavs, sr = model.generate_voice_design(text=t, language="English", instruct=INSTRUCT)
    w = np.asarray(wavs[0], dtype=np.float32).reshape(-1)
    chunks.append(w)
    sr_out = int(sr)
    print("seg", i, round(len(w) / sr, 1), "s audio in", round(time.time() - t0), "s", flush=True)
os.makedirs("out", exist_ok=True)
join(chunks, sr_out, f"out/{ID}.wav")
