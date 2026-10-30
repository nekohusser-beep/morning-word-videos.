#!/usr/bin/env python3
"""Word-check the sung audio against the exact KJV text with Whisper (faster-whisper small.en, CPU).
Usage: check.py <short|full> <outdir>. Writes <outdir>/<case>-check.txt. Sung vocals over a bed are hard for Whisper,
so a miss can be the singer OR Whisper; the report lists both sides so a human ear decides."""
import difflib
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lyrics import plain_for  # noqa: E402

case, out = sys.argv[1], Path(sys.argv[2])
mp3 = out / f"{case}.mp3"
norm = lambda s: re.findall(r"[a-z']+", s.lower().replace("\u2019", "'"))  # noqa: E731
ref = norm(plain_for(case))

from faster_whisper import WhisperModel  # noqa: E402

segs, info = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(str(mp3), language="en", beam_size=5, vad_filter=False)
text = " ".join(s.text for s in segs)
hyp = norm(text)

sm = difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False)
ok = sum(b.size for b in sm.get_matching_blocks())
lines = [f"case={case} ref_words={len(ref)} heard_words={len(hyp)} matched_words={ok} match_rate={ok / max(1, len(ref)):.2f}"]
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)], capture_output=True, text=True).stdout.strip()
lines.append(f"audio_duration_s={dur}")
vol = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp3), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
m = re.search(r"I:\s+(-?[\d.]+) LUFS", vol[::-1][:0] or vol[vol.rfind("Integrated loudness"):])
lines.append("loudness=" + (m.group(1) + " LUFS" if m else "n/a"))
lines.append("--- diff (ref -> heard) ---")
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag != "equal":
        lines.append(f"{tag}: MISSING/CHANGED '{' '.join(ref[i1:i2])}' -> HEARD '{' '.join(hyp[j1:j2])}'")
lines.append("--- whisper transcript ---")
lines.append(text.strip())
(out / f"{case}-check.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[:3]))
