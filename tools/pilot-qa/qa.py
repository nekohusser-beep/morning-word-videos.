import glob, json, subprocess, sys, traceback
import numpy as np
from faster_whisper import WhisperModel

out, txt, log = {}, [], []
model = None
for name in ("large-v3", "medium.en", "small.en"):
    try:
        model = WhisperModel(name, device="cpu", compute_type="int8")
        log.append("model " + name + " loaded")
        break
    except Exception:
        log.append("model " + name + " failed:\n" + traceback.format_exc())
if model is not None:
    for f in sorted(glob.glob("in/*.mp3")):
        try:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
            audio = np.frombuffer(raw, dtype=np.float32)
            segs, _ = model.transcribe(audio, language="en", word_timestamps=True, beam_size=5)
            words = [[round(w.start, 2), round(w.end, 2), w.word.strip()] for s in segs for w in s.words]
            out[f] = words
            txt.append("== " + f + "\n" + " ".join(w[2] for w in words) + "\n")
        except Exception:
            log.append("transcribe " + f + " failed:\n" + traceback.format_exc())
open("pilot-qa.txt", "w").write("\n".join(txt))
json.dump(out, open("pilot-qa.json", "w"))
open("pilot-qa.log", "w").write("\n".join(log))
print("\n".join(log))
print("\n".join(txt))
