"""KittenTTS mini 0.8 (80M, Apache-2.0) CPU test: Psalm 23:1-3 KJV with each male-sounding preset voice.
Writes out/KT_<voice>.wav and out/KT_summary.json (audio seconds, compute seconds, real-time factor, peak RAM)."""
import os, time, json, resource, traceback
import numpy as np, soundfile as sf
from kittentts import KittenTTS

OUT = "out"
os.makedirs(OUT, exist_ok=True)
# Psalm 23:1-3 KJV, word for word. "Lord" is written in normal case here only so the voice says a word, not the letters L-O-R-D.
TEXT = ("The Lord is my shepherd; I shall not want. "
        "He maketh me to lie down in green pastures: he leadeth me beside the still waters. "
        "He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake.")
t0 = time.time()
m = KittenTTS("KittenML/kitten-tts-mini-0.8")
summary = {"load_s": round(time.time() - t0, 1), "voices_available": str(getattr(m, "available_voices", None)), "runs": []}
print("loaded in", summary["load_s"], "s; voices:", summary["voices_available"], flush=True)
for v in ["Bruno", "Hugo", "Leo", "Jasper"]:
    try:
        ts = time.time()
        a = np.asarray(m.generate(TEXT, voice=v), dtype=np.float32).reshape(-1)
        el, dur = time.time() - ts, len(a) / 24000
        sf.write(f"{OUT}/KT_{v}.wav", a, 24000)
        summary["runs"].append({"voice": v, "audio_s": round(dur, 1), "compute_s": round(el, 1), "rtf": round(el / dur, 2)})
        print(v, round(dur, 1), "s audio in", round(el, 1), "s, rtf", round(el / dur, 2), flush=True)
    except Exception:
        traceback.print_exc()
summary["peak_ram_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
json.dump(summary, open(f"{OUT}/KT_summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1), flush=True)
