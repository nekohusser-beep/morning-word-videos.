"""Make SYNTHETIC reference voices (Kokoro, Apache-2.0) for the CosyVoice 3 test.
No real person is cloned. Output: refs/R1.wav, R2.wav, R3.wav + refs/meta.json (voice name and exact transcript)."""
import json, os, sys, traceback
import soundfile as sf
from kokoro_onnx import Kokoro

REF_TEXT = ("The morning is quiet, and the light comes in slow and gentle. "
            "Take a breath, and listen well, because the word of the Lord is good.")
VOICES = {"R1": "am_fenrir", "R2": "bm_george", "R3": "am_liam"}

k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
os.makedirs("refs", exist_ok=True)
meta = {}
for rid, v in VOICES.items():
    try:
        lang = "en-gb" if v.startswith("b") else "en-us"
        samples, sr = k.create(REF_TEXT, voice=v, speed=0.9, lang=lang)
        sf.write(f"refs/{rid}.wav", samples, sr)
        meta[rid] = {"voice": v, "text": REF_TEXT, "sr": int(sr), "sec": round(len(samples) / sr, 1)}
        print("ref", rid, v, meta[rid]["sec"], "s", flush=True)
    except Exception:
        traceback.print_exc()
if not meta:
    sys.exit("no reference voice was made")
json.dump(meta, open("refs/meta.json", "w"), indent=1)
