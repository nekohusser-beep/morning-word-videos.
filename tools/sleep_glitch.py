#!/usr/bin/env python3
"""Glitch scan for Kokoro-rendered sleep chapters.

Each chapter FLAC is: header ("Psalm N." / "Chapter N."), 3.5 s gap, then every verse
spoken on its own with 2.5 s of silence after it. So long silences (>= 2.0 s) split the file
into one speech block per verse, and anything quieter inside a block is the narrator.

Per chapter this reports:
  block_mismatch  - number of speech blocks != 1 + verses (a verse got split or two merged)
  rate outliers   - verses spoken much faster/slower than the book's median (characters per speech second)
  mid_pauses      - silences of >= PAUSE s inside a verse
  clicks          - sample spikes that stand far above the local level
  garbled         - verses whose transcript disagrees with the KJV text, or with very low-confidence words

usage: sleep_glitch.py BOOK.json FLAC_DIR OUT.json [whisper_model] [i N]
"""
import json, os, re, subprocess, sys, difflib, statistics
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

PAUSE = 1.1          # seconds of silence inside a verse that counts as a mid-verse pause
SPLIT = 2.0          # silence that separates verses
RATE_Z = 3.0         # robust z-score for a rushed / dragged verse
CLICK_K = 14.0       # spike height vs local RMS
LOWP = 0.30          # word probability treated as garbled

book_json, flac_dir, out_path = sys.argv[1:4]
model_name = sys.argv[4] if len(sys.argv) > 4 else "medium.en"
book = json.load(open(book_json))
chs = {int(c["chapter"]): c for c in book["chapters"]}
label = "Psalm" if os.path.basename(book_json).startswith("Psalms") else "Chapter"
norm = lambda s: re.sub(r"[^a-z0-9' ]", " ", s.lower().replace("’", "'")).split()


def silences(path, noise="-45dB", d=0.5):
    err = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", f"silencedetect=n={noise}:d={d}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    total = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3))
    out = []
    for i, s in enumerate(st):
        e = en[i] if i < len(en) else total
        out.append((max(0.0, s), e))
    return out, total


def blocks(sils, total):
    """speech blocks = gaps between silences of >= SPLIT."""
    seps = [s for s in sils if s[1] - s[0] >= SPLIT]
    res, cur = [], 0.0
    for s, e in seps:
        if s - cur > 0.15:
            res.append((cur, s))
        cur = e
    if total - cur > 0.15:
        res.append((cur, total))
    return res


def clicks_in(y, sr, t0, t1):
    seg = y[int(t0 * sr):int(t1 * sr)]
    if len(seg) < sr // 2:
        return []
    d = np.abs(np.diff(seg))
    win = sr // 20
    k = np.ones(win) / win
    local = np.sqrt(np.convolve(d * d, k, mode="same")) + 1e-6
    hits = np.where((d > CLICK_K * local) & (d > 0.04))[0]
    out, last = [], -10**9
    for h in hits:
        if h - last > sr // 4:
            out.append(round(t0 + h / sr, 2))
        last = h
    return out[:6]


model = WhisperModel(model_name, device="cpu", compute_type="int8")
report, rates_all = [], []
files = sorted(f for f in os.listdir(flac_dir) if f.endswith(".flac"))
for f in files:
    n = int(f[:3])
    if n == 0:
        continue
    path = os.path.join(flac_dir, f)
    sils, total = silences(path)
    bl = blocks(sils, total)
    verses = chs[n]["verses"]
    r = {"file": f, "chapter": n, "verses": len(verses), "blocks": len(bl), "issues": []}
    if len(bl) != len(verses) + 1:
        r["issues"].append({"type": "block_mismatch", "detail": f"{len(bl)} speech blocks vs {len(verses) + 1} expected"})
    y, sr = sf.read(path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    segs, _ = model.transcribe(path, language="en", beam_size=5, vad_filter=False,
                               condition_on_previous_text=False, word_timestamps=True)
    words = [w for s in segs for w in s.words]
    for vi, v in enumerate(verses):
        bi = vi + 1
        if bi >= len(bl):
            r["issues"].append({"type": "missing_block", "verse": vi + 1})
            continue
        t0, t1 = bl[bi]
        speech = t1 - t0
        chars = len(v["text"].strip())
        rate = chars / max(speech, 0.1)
        rates_all.append((n, vi + 1, rate))
        inner = [(s, e) for s, e in sils if s >= t0 and e <= t1 and (e - s) >= PAUSE]
        for s, e in inner:
            r["issues"].append({"type": "mid_pause", "verse": vi + 1, "at": round(s, 1), "seconds": round(e - s, 2)})
        for c in clicks_in(y, sr, t0, t1):
            r["issues"].append({"type": "click", "verse": vi + 1, "at": c})
        hw = [w for w in words if w.start >= t0 - 0.2 and w.end <= t1 + 0.2]
        heard = norm(" ".join(w.word for w in hw))
        ref = norm(v["text"])
        sm = difflib.SequenceMatcher(a=ref, b=heard, autojunk=False)
        bad = sum(max(a2 - a1, b2 - b1) for op, a1, a2, b1, b2 in sm.get_opcodes() if op != "equal")
        low = [w.word.strip() for w in hw if w.probability < LOWP]
        if bad / max(1, len(ref)) > 0.12 or len(low) >= 2:
            r["issues"].append({"type": "garbled", "verse": vi + 1, "mismatch_words": bad, "low_conf": low[:5],
                                "start": round(t0, 1)})
    report.append(r)
    print(f, len(bl), len(r["issues"]), flush=True)

# rate outliers: robust z-score against the whole set of verses in this run
vals = [x[2] for x in rates_all]
if len(vals) > 20:
    med = statistics.median(vals)
    mad = statistics.median(abs(x - med) for x in vals) or 1e-6
    by = {r["chapter"]: r for r in report}
    for n, vn, rt in rates_all:
        z = 0.6745 * (rt - med) / mad
        if abs(z) >= RATE_Z:
            by[n]["issues"].append({"type": "rushed" if z > 0 else "dragged", "verse": vn,
                                    "chars_per_sec": round(rt, 1), "z": round(z, 1), "median": round(med, 1)})
json.dump({"model": model_name, "chapters": report}, open(out_path, "w"), indent=1)
