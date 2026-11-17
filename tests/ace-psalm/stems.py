#!/usr/bin/env python3
"""Whisper word timestamps on a separated VOCALS stem (cleaner than the full mix).
Usage: stems.py <vocals.mp3|wav> <out_words.json>. Never crashes the job: errors go into the json."""
import json
import subprocess
import sys
import traceback

import numpy as np

src, out = sys.argv[1], sys.argv[2]
res = {"file": src, "words": [], "error": None}
try:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", src, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
        capture_output=True, check=True,
    ).stdout
    audio = np.frombuffer(raw, np.float32)
    res["seconds"] = round(len(audio) / 16000, 2)
    from faster_whisper import WhisperModel

    model = WhisperModel("medium.en", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(
        audio, language="en", beam_size=5, word_timestamps=True,
        condition_on_previous_text=False, vad_filter=False,
    )
    for s in segs:
        for w in s.words or []:
            res["words"].append({"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2), "p": round(w.probability, 2)})
except Exception:  # noqa: BLE001
    res["error"] = traceback.format_exc()
json.dump(res, open(out, "w"), indent=0)
print("words:", len(res["words"]), "error:", bool(res["error"]))
