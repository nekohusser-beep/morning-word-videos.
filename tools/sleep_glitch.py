#!/usr/bin/env python3
"""Per-verse measurements for Kokoro-rendered sleep chapters (v2: DP alignment, raw numbers).

Each chapter FLAC is: header ("Psalm N." / "Chapter N."), 3.5 s gap, then every verse spoken on
its own with 2.5 s of silence after it. Silences >= 2.0 s split the file into speech blocks. A verse
can come out as 2+ blocks (a >= 2 s pause inside it), so verses are aligned to blocks by dynamic
programming on expected duration (chars / 9.5 per second), allowing a verse to take 1-3 blocks.

For every verse the report stores raw numbers; thresholds are applied afterwards:
  k            blocks the verse took (k > 1 = long mid-verse pause)
  cps          characters per second of the verse's span (speed)
  max_pause    longest silence inside the verse span (>= 0.5 s)
  click        biggest spike-to-local-level ratio in the span, and its time
  mismatch     words that differ from the KJV text / words in the verse (whisper transcript)
  low          words whisper heard with probability < 0.30

usage: sleep_glitch.py BOOK.json FLAC_DIR OUT.json [whisper_model]
"""
import json, os, re, subprocess, sys, difflib, functools
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

book_json, flac_dir, out_path = sys.argv[1:4]
model_name = sys.argv[4] if len(sys.argv) > 4 else "medium.en"
book = json.load(open(book_json))
chs = {int(c["chapter"]): c for c in book["chapters"]}
norm = lambda s: re.sub(r"[^a-z0-9' ]", " ", s.lower().replace("’", "'")).split()
SPLIT = 2.0
CPS = 9.5


def silences(path):
    err = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "silencedetect=n=-45dB:d=0.5", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    total = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3))
    return [(max(0.0, s), (en[i] if i < len(en) else total)) for i, s in enumerate(st)], total


def blocks(sils, total):
    res, cur = [], 0.0
    for s, e in sils:
        if e - s >= SPLIT:
            if s - cur > 0.15:
                res.append((cur, s))
            cur = e
    if total - cur > 0.15:
        res.append((cur, total))
    return res


def align(texts, B):
    n, m = len(texts), len(B)
    INF = 1e9

    @functools.lru_cache(None)
    def f(i, j):
        if i == n:
            return (0.0, ()) if j == m else (INF, ())
        if j >= m:
            return (INF, ())
        best = (INF, ())
        e = len(texts[i]) / CPS
        for k in (1, 2, 3):
            if j + k > m:
                break
            span = B[j + k - 1][1] - B[j][0]
            cost = abs(span - e) / e + (0.15 if k > 1 else 0.0)
            c, p = f(i + 1, j + k)
            if c + cost < best[0]:
                best = (c + cost, (k,) + p)
        return best

    return f(0, 0)[1]


def click_peak(y, sr, t0, t1):
    seg = y[int(t0 * sr):int(t1 * sr)]
    if len(seg) < sr // 2:
        return 0.0, 0.0
    d = np.abs(np.diff(seg))
    win = sr // 20
    local = np.sqrt(np.convolve(d * d, np.ones(win) / win, mode="same")) + 1e-4
    ratio = np.where(d > 0.03, d / local, 0.0)
    h = int(np.argmax(ratio))
    return float(ratio[h]), round(t0 + h / sr, 2)


model = WhisperModel(model_name, device="cpu", compute_type="int8")
report = []
for f in sorted(x for x in os.listdir(flac_dir) if x.endswith(".flac")):
    n = int(f[:3])
    if n == 0:
        continue
    path = os.path.join(flac_dir, f)
    sils, total = silences(path)
    bl = blocks(sils, total)
    verses = [v["text"].strip() for v in chs[n]["verses"]]
    B = bl[1:]
    plan = align(verses, B)
    r = {"chapter": n, "verses": len(verses), "blocks": len(bl), "aligned": bool(plan), "v": []}
    if not plan:
        report.append(r)
        print(f, "ALIGN FAILED", flush=True)
        continue
    y, sr = sf.read(path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    segs, _ = model.transcribe(path, language="en", beam_size=5, vad_filter=False,
                               condition_on_previous_text=False, word_timestamps=True)
    words = [w for s in segs for w in s.words]
    j = 0
    for vi, k in enumerate(plan):
        t0, t1 = B[j][0], B[j + k - 1][1]
        j += k
        inner = [e - s for s, e in sils if s >= t0 - 0.05 and e <= t1 + 0.05 and e - s >= 0.5 and e - s < SPLIT]
        inner += [B[j - k + q + 1][0] - B[j - k + q][1] for q in range(k - 1)]
        cr, ct = click_peak(y, sr, t0, t1)
        hw = [w for w in words if w.start >= t0 - 0.25 and w.end <= t1 + 0.25]
        heard, ref = norm(" ".join(w.word for w in hw)), norm(verses[vi])
        sm = difflib.SequenceMatcher(a=ref, b=heard, autojunk=False)
        bad = sum(max(a2 - a1, b2 - b1) for op, a1, a2, b1, b2 in sm.get_opcodes() if op != "equal")
        r["v"].append({"n": vi + 1, "k": k, "t0": round(t0, 1), "t1": round(t1, 1),
                       "cps": round(len(verses[vi]) / max(t1 - t0, 0.1), 2),
                       "max_pause": round(max(inner), 2) if inner else 0.0,
                       "click": round(cr, 1), "click_at": ct,
                       "mismatch": round(bad / max(1, len(ref)), 3),
                       "low": [w.word.strip() for w in hw if w.probability < 0.30][:6]})
    report.append(r)
    print(f, len(bl), sum(1 for v in r["v"] if v["k"] > 1), flush=True)
json.dump({"model": model_name, "chapters": report}, open(out_path, "w"))
