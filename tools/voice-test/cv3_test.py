"""CosyVoice 3 (Fun-CosyVoice3-0.5B-2512, Apache-2.0) CPU test: Psalm 23:1-3 KJV in a voice cloned from a SYNTHETIC reference.
Run from inside the CosyVoice checkout:  cd cv && python ../tools/voice-test/cv3_test.py
Writes ../out/CV3_<ref>.wav and ../out/CV3_summary.json (load time, per-line audio seconds, compute seconds, real-time factor, peak RAM)."""
import os, sys, time, json, resource, traceback, subprocess
sys.path.insert(0, os.getcwd())
sys.path.append("third_party/Matcha-TTS")
import numpy as np, soundfile as sf, torch
torch.set_num_threads(os.cpu_count() or 4)
from cosyvoice.cli.cosyvoice import AutoModel

MD = "pretrained_models/Fun-CosyVoice3-0.5B"
OUT = "../out"
os.makedirs(OUT, exist_ok=True)
# Psalm 23:1-3 KJV, word for word. "Lord" is written in normal case here only so the voice says a word, not the letters L-O-R-D.
SEGS = [
    "The Lord is my shepherd; I shall not want.",
    "He maketh me to lie down in green pastures: he leadeth me beside the still waters.",
    "He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake.",
]
PREFIX = "You are a helpful assistant.<|endofprompt|>"

t0 = time.time()
model = AutoModel(model_dir=MD)
load_s = round(time.time() - t0, 1)
sr = int(model.sample_rate)
print("model loaded in", load_s, "s; sample rate", sr, "; threads", torch.get_num_threads(), flush=True)

meta = json.load(open("../refs/meta.json"))
summary = {"load_s": load_s, "sample_rate": sr, "threads": torch.get_num_threads(), "runs": []}
for rid, m in meta.items():
    wav = f"../refs/{rid}.wav"
    chunks, per = [], []
    t_run = time.time()
    for i, seg in enumerate(SEGS):
        ts = time.time()
        mode = "zero_shot"
        try:
            parts = [j["tts_speech"].squeeze(0).numpy() for j in model.inference_zero_shot(seg, PREFIX + m["text"], wav, stream=False)]
        except Exception:
            traceback.print_exc()
            mode = "cross_lingual"
            parts = [j["tts_speech"].squeeze(0).numpy() for j in model.inference_cross_lingual(PREFIX + seg, wav, stream=False)]
        a = np.concatenate(parts).astype(np.float32)
        dur, el = len(a) / sr, time.time() - ts
        per.append({"line": i + 1, "mode": mode, "audio_s": round(dur, 1), "compute_s": round(el, 1), "rtf": round(el / dur, 2)})
        print("ref", rid, "line", i + 1, mode, round(dur, 1), "s audio in", round(el, 1), "s, rtf", round(el / dur, 2), flush=True)
        chunks += [a, np.zeros(int(sr * 0.8), dtype=np.float32)]
    full = np.concatenate(chunks)
    pk = float(np.abs(full).max()) or 1.0
    if pk > 0.97:
        full = full * (0.97 / pk)
    sf.write(f"{OUT}/CV3_{rid}.wav", full, sr)
    tot = time.time() - t_run
    summary["runs"].append({"ref": rid, "ref_voice": m["voice"], "audio_s": round(len(full) / sr, 1), "compute_s": round(tot, 1), "rtf": round(tot / (len(full) / sr), 2), "lines": per})
    print("wrote", f"{OUT}/CV3_{rid}.wav", round(len(full) / sr, 1), "s", flush=True)

summary["peak_ram_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
summary["model_dir_size"] = subprocess.run(["du", "-sh", MD], capture_output=True, text=True).stdout.split()[0]
json.dump(summary, open(f"{OUT}/CV3_summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1), flush=True)
