#!/usr/bin/env python3
"""Word-check the sung audio against the exact KJV text with Whisper (faster-whisper small.en, CPU).
Usage: check.py <short|full> <outdir>. Writes <outdir>/<case>-check.txt. NEVER crashes: every stage is wrapped and the
traceback goes into the file, so a failure is readable from the ace-out branch. Sung vocals over a bed are hard for Whisper,
so a miss can be the singer OR Whisper; a human ear decides."""
import difflib
import re
import subprocess
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
case, out = sys.argv[1], Path(sys.argv[2])
mp3 = out / f"{case}.mp3"
rep = out / f"{case}-check.txt"
lines = []


def flush():
    rep.write_text("\n".join(lines) + "\n", encoding="utf-8")


def stage(name, fn):
    try:
        fn()
    except BaseException:  # noqa: BLE001
        lines.append(f"!! stage '{name}' failed:\n{traceback.format_exc()}")
    flush()


def facts():
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)],
                         capture_output=True, text=True).stdout.strip()
    lines.append(f"case={case} audio_duration_s={dur}")
    vol = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp3), "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    tail = vol[vol.rfind("Summary"):] if "Summary" in vol else vol[-600:]
    m = re.search(r"I:\s+(-?[\d.]+)\s+LUFS", tail)
    lines.append("integrated_loudness=" + (m.group(1) + " LUFS" if m else "n/a"))


def whisper():
    from lyrics import plain_for
    from faster_whisper import WhisperModel
    norm = lambda s: re.findall(r"[a-z']+", s.lower().replace("\u2019", "'"))  # noqa: E731
    ref = norm(plain_for(case))
    import numpy as np  # decode with ffmpeg ourselves: faster-whisper's PyAV decoder crashed on the runner (av.open metadata_errors)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    audio = np.frombuffer(raw, dtype=np.float32)
    lines.append(f"decoded_samples={len(audio)} ({len(audio) / 16000:.1f} s at 16 kHz)")
    segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(audio, language="en", beam_size=5)
    text = " ".join(s.text for s in segs)
    hyp = norm(text)
    sm = difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False)
    ok = sum(b.size for b in sm.get_matching_blocks())
    lines.append(f"ref_words={len(ref)} heard_words={len(hyp)} matched_words={ok} match_rate={ok / max(1, len(ref)):.2f}")
    lines.append("--- diff (KJV -> heard) ---")
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            lines.append(f"{tag}: KJV '{' '.join(ref[i1:i2])}' -> HEARD '{' '.join(hyp[j1:j2])}'")
    lines.append("--- whisper transcript ---")
    lines.append(text.strip())


stage("facts", facts)
stage("whisper", whisper)
print("\n".join(lines[:6]))
sys.exit(0)
