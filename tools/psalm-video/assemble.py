#!/usr/bin/env python3
"""CALL AND RESPONSE song assembler (free: numpy, scipy, ffmpeg).

Neko's design (Oct 30 2026 2:36 AM ET): the baritone sings a line, the angels (altos) answer the SAME line right after,
he comes back in, they answer again, all over ONE unbroken music bed, so there is never dead air.

Inputs (from the ace-out branch, produced by .github/workflows/ace-stems.yml):
  <aceout>/<case>/<case>-vocals.mp3   voice stem of a sung take
  <aceout>/<case>/<case>-words.json   Whisper word timestamps on that stem
  <aceout>/<case>/<case>-bed.mp3      music-only stem (ffull cases)
Every line is picked from the take that sang it best (exact KJV words, scored against the reference), cut on a quiet frame, and placed on the timeline.
Choir = best line from the alto takes (cases starting with 'c') when there is a good one, else the lead voice lifted into an alto/soprano choir.

Usage: assemble.py --aceout DIR --out OUTDIR [--intro 9 --gap 0.35 --verse-gap 0.9]
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import scipy.signal as ss

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests" / "ace-psalm"))
from lyrics import CASES, LINES, V  # noqa: E402

SR = 44100
ap = argparse.ArgumentParser()
ap.add_argument("--aceout", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--intro", type=float, default=9.0)
ap.add_argument("--gap", type=float, default=0.35, help="seconds between a choir answer's end and the next lead line (inside a verse)")
ap.add_argument("--verse-gap", type=float, default=0.9)
ap.add_argument("--outro", type=float, default=9.0)
ap.add_argument("--bed", default="", help="force a bed case, e.g. ffull150_c")
ap.add_argument("--choir", default="auto", choices=["auto", "alto", "lift"])
a = ap.parse_args()
OUT = Path(a.out)
OUT.mkdir(parents=True, exist_ok=True)
ACE = Path(a.aceout)


def log(*x):
    print(*x, flush=True)


def decode(path, ar=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(ar), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def norm(w):
    return re.sub(r"[^a-z']", "", w.lower())


# ---------- reference lines ----------
GLOBAL = [(v, k) for v in range(6) for k in range(len(LINES[v]))]
REFW = {g: [norm(w) for w in LINES[g[0]][g[1]].split()] for g in GLOBAL}
VOCAB = sorted({w for ws in REFW.values() for w in ws})


def case_lines(case):
    c = CASES[case]
    vs = [V.index(x) for x in c["verses"]]
    return [(v, k) for v in vs for k in range(len(LINES[v]))]


# ---------- candidates ----------
class Take:
    def __init__(self, case):
        self.case = case
        d = ACE / case
        self.words = json.load(open(d / f"{case}-words.json"))["words"]
        self.wav = decode(d / f"{case}-vocals.mp3")
        mono = self.wav.mean(axis=1)
        hop = int(SR * 0.005)
        n = len(mono) // hop
        self.env = np.sqrt((mono[: n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
        self.hop = hop
        self.cands = {}
        self.align()

    def align(self):
        lines = case_lines(self.case)
        ref, owner = [], []
        for g in lines:
            for w in REFW[g]:
                ref.append(w)
                owner.append(g)
        heard = []
        for w in self.words:
            n = norm(w["w"])
            if not n:
                continue
            m = difflib.get_close_matches(n, VOCAB, n=1, cutoff=0.84)
            heard.append((m[0] if m else n, w))
        hs = [h[0] for h in heard]
        sm = difflib.SequenceMatcher(None, ref, hs, autojunk=False)
        mp = {}
        for blk in sm.get_matching_blocks():
            for i in range(blk.size):
                mp[blk.a + i] = blk.b + i
        pos = 0
        for g in lines:
            n = len(REFW[g])
            idx = [mp[p] for p in range(pos, pos + n) if p in mp]
            first_ok = pos in mp
            last_ok = (pos + n - 1) in mp
            pos += n
            if len(idx) < max(2, int(0.5 * n)):
                continue
            h0, h1 = min(idx), max(idx)
            extras = (h1 - h0 + 1) - len(idx)
            prob = float(np.mean([heard[i][1]["p"] for i in idx]))
            dur = heard[h1][1]["e"] - heard[h0][1]["s"]
            prev_end = heard[h0 - 1][1]["e"] if h0 > 0 else 0.0
            next_start = heard[h1 + 1][1]["s"] if h1 + 1 < len(heard) else len(self.wav) / SR
            cov = len(idx) / n
            score = cov + (0.2 if first_ok and last_ok else 0) - 0.05 * extras + 0.15 * prob - (0.15 if dur > 9 else 0) - (0.2 if dur < 1.0 * n * 0.25 else 0)
            self.cands[g] = dict(case=self.case, cov=cov, score=score, extras=extras, t0=heard[h0][1]["s"], t1=heard[h1][1]["e"], prev_end=prev_end, next_start=next_start, dur=dur)

    def low(self, t0, t1):
        i0, i1 = max(0, int(t0 * SR / self.hop)), min(len(self.env), int(t1 * SR / self.hop) + 1)
        if i1 <= i0:
            return t0
        return (i0 + int(np.argmin(self.env[i0:i1]))) * self.hop / SR

    def cut(self, g):
        c = self.cands[g]
        s = self.low(max(c["t0"] - 0.35, c["prev_end"]), c["t0"] - 0.02)
        e = self.low(c["t1"] + 0.05, min(c["t1"] + 0.55, c["next_start"]))
        if e <= s + 0.5:
            s, e = c["t0"] - 0.05, c["t1"] + 0.25
        seg = self.wav[int(s * SR): int(e * SR)].copy()
        seg, self.removed = tighten(seg)
        fi, fo = int(0.03 * SR), int(0.12 * SR)
        seg[:fi] *= np.linspace(0, 1, fi)[:, None]
        seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
        return seg


def tighten(seg, min_run=0.7, keep=0.2, xf=0.04):
    """Voice-stem only: shorten any silence longer than min_run inside a line to 2*keep, so the singer never stalls mid-line."""
    hop = int(SR * 0.01)
    n = len(seg) // hop
    if n < 10:
        return seg, 0.0
    env = np.sqrt((seg[: n * hop].mean(axis=1).reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
    thr = np.percentile(env, 95) * 0.02
    quiet = env < thr
    cuts, i = [], 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if i > 0 and j < n and (j - i) * 0.01 > min_run:
                cuts.append((i + int(keep / 0.01), j - int(keep / 0.01)))
            i = j
        else:
            i += 1
    if not cuts:
        return seg, 0.0
    out, pos, removed = [], 0, 0
    x = int(xf * SR)
    for a0, a1 in cuts:
        p0, p1 = a0 * hop, a1 * hop
        out.append(seg[pos:p0])
        pos = p1
        removed += (p1 - p0) / SR
    out.append(seg[pos:])
    res = out[0]
    for part in out[1:]:
        k = min(x, len(res), len(part))
        fade = np.linspace(0, 1, k)[:, None]
        res = np.vstack([res[:-k], res[-k:] * (1 - fade) + part[:k] * fade, part[k:]])
    return res, removed


def rms_db(x):
    r = np.sqrt((x ** 2).mean() + 1e-12)
    return 20 * np.log10(r + 1e-12)


def set_rms(x, target_db, clamp=14):
    g = np.clip(target_db - rms_db(x), -clamp, clamp)
    return x * (10 ** (g / 20))


def lift(seg, pitch_ratio, formant):
    with tempfile.TemporaryDirectory() as td:
        i, o = Path(td) / "i.wav", Path(td) / "o.wav"
        pcm = (np.clip(seg, -1, 1) * 32767).astype("<i2")
        import wave
        with wave.open(str(i), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes(pcm.tobytes())
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(i), "-af", f"rubberband=pitch={pitch_ratio}:formant={formant}", str(o)], check=True)
        return decode(o)


def make_ir(rt60=3.0, seed=7):
    rng = np.random.default_rng(seed)
    n = int(SR * rt60)
    t = np.arange(n) / SR
    env = np.exp(-6.9 * t / rt60)
    ir = np.stack([rng.standard_normal(n) * env, rng.standard_normal(n) * env], axis=1)
    b, aa = ss.butter(2, 5500 / (SR / 2))
    ir = ss.lfilter(b, aa, ir, axis=0)
    pre = int(0.03 * SR)
    ir = np.vstack([np.zeros((pre, 2)), ir]).astype(np.float32)
    return ir / np.sqrt((ir ** 2).sum() / 2)


def reverb(x, ir, wet):
    n = len(x)
    w = np.stack([ss.fftconvolve(x[:, c], ir[:, c]) for c in range(2)], axis=1)
    w = w / (np.abs(w).max() + 1e-9) * np.abs(x).max()
    out = np.zeros((n, 2), np.float32)
    out += x * (1 - wet)
    out += w[:n] * wet  # the reverb tail past the end is covered by the outro fade
    return out


# ---------- load takes ----------
cases = sorted(p.name for p in ACE.iterdir() if (p / f"{p.name}-words.json").exists() and (p / f"{p.name}-vocals.mp3").exists())
lead_cases = [c for c in cases if c.startswith(("ffull", "fp"))]
choir_cases = [c for c in cases if c.startswith(("cfull", "cp"))]
log("lead takes:", lead_cases)
log("choir takes:", choir_cases)
takes = {}
for c in lead_cases + choir_cases:
    try:
        takes[c] = Take(c)
    except Exception as e:  # noqa: BLE001
        log("skip", c, repr(e))

plan, lead_pick, choir_pick = [], {}, {}
for g in GLOBAL:
    pool = sorted([t.cands[g] for c, t in takes.items() if c in lead_cases and g in t.cands], key=lambda d: -d["score"])
    cpool = sorted([t.cands[g] for c, t in takes.items() if c in choir_cases and g in t.cands], key=lambda d: -d["score"])
    if not pool:
        log("NO LEAD CANDIDATE for", g)
        sys.exit(2)
    lead_pick[g] = pool[0]
    runner = pool[1] if len(pool) > 1 else pool[0]
    choir_pick[g] = (cpool[0], "alto") if (cpool and cpool[0]["cov"] >= 0.7 and a.choir != "lift") else (runner, "lift")
    if a.choir == "alto" and cpool:
        choir_pick[g] = (cpool[0], "alto")

# ---------- bed ----------
def bed_quality(case):
    p = ACE / case / f"{case}-bed.mp3"
    if not p.exists():
        return -1, None
    b = decode(p)
    r = np.sqrt((b[: len(b) // SR * SR].reshape(-1, SR, 2) ** 2).mean(axis=(1, 2)) + 1e-12)
    mid = r[10: max(len(r) - 10, 11)]
    if len(mid) < 20:
        return -1, b
    steady = np.percentile(mid, 10) / (np.median(mid) + 1e-9)
    return float(steady), b


beds = {}
for c in cases:
    q, b = bed_quality(c)
    if b is not None:
        beds[c] = (q, b)
log("bed steadiness:", {k: round(v[0], 2) for k, v in beds.items()})
bed_case = a.bed or max(beds, key=lambda k: beds[k][0])
bed = beds[bed_case][1]
log("bed chosen:", bed_case, round(len(bed) / SR, 1), "s")

# ---------- build ----------
IR = make_ir()
LEAD_DB, CHOIR_DB = -19.0, -22.0
leads, answers = {}, {}
lead_removed_map = {}
for g in GLOBAL:
    lp = lead_pick[g]
    leads[g] = set_rms(takes[lp["case"]].cut(g), LEAD_DB)
    lead_removed_map[g] = takes[lp["case"]].removed
    cp, kind = choir_pick[g]
    seg = takes[cp["case"]].cut(g)
    if kind == "alto":
        ans = set_rms(seg, CHOIR_DB)
    else:  # lift the voice into an alto + a quieter soprano shimmer
        alto = lift(seg, 1.4983, "shifted")  # up a fifth, formants follow = lighter, female-leaning
        sop = lift(seg, 2.0, "preserved")  # up an octave, quieter
        n = max(len(alto), len(sop))
        m = np.zeros((n, 2), np.float32)
        m[: len(alto)] += alto * 1.0
        m[: len(sop)] += sop * 0.5
        # a little left/right spread so it sounds like several voices
        d = int(0.022 * SR)
        m2 = m.copy()
        m2[d:, 0] = m[:-d, 0]
        m2[:-d, 1] = m[d:, 1]
        ans = set_rms((m + m2) * 0.5, CHOIR_DB)
    answers[g] = ans

t = a.intro
events = []
lead_bus = np.zeros((int((a.intro + 400) * SR), 2), np.float32)
choir_bus = np.zeros_like(lead_bus)
verse_first = {}
for n, g in enumerate(GLOBAL):
    L, A = leads[g], answers[g]
    s0 = int(t * SR)
    lead_bus[s0: s0 + len(L)] += L
    lead_end = t + len(L) / SR
    ca = lead_end + 0.12
    s1 = int(ca * SR)
    choir_bus[s1: s1 + len(A)] += A
    ans_end = ca + len(A) / SR
    events.append(dict(line=list(g), text=LINES[g[0]][g[1]], lead_start=round(t, 2), lead_end=round(lead_end, 2), choir_start=round(ca, 2), choir_end=round(ans_end, 2),
                       lead_removed_s=round(lead_removed_map[g], 2), lead_take=lead_pick[g]["case"], lead_cov=round(lead_pick[g]["cov"], 2), choir_take=choir_pick[g][0]["case"], choir_kind=choir_pick[g][1], choir_cov=round(choir_pick[g][0]["cov"], 2)))
    verse_first.setdefault(g[0], t)
    nxt = GLOBAL[n + 1] if n + 1 < len(GLOBAL) else None
    t = ans_end - 0.25 + (a.verse_gap if (nxt and nxt[0] != g[0]) else a.gap)
voice_end = events[-1]["choir_end"]
total = voice_end + a.outro
N = int(total * SR)
lead_bus, choir_bus = lead_bus[:N], choir_bus[:N]

# bed: loop with a 6 s crossfade if the stem is shorter than needed
need = N
b = bed
if len(b) < need:
    xf = 6 * SR
    core = b[8 * SR: len(b) - 4 * SR]
    out = b[: len(b) - 4 * SR].copy()
    while len(out) < need + xf:
        fade = np.linspace(0, 1, xf)[:, None]
        out[-xf:] = out[-xf:] * (1 - fade) + core[:xf] * fade
        out = np.vstack([out, core[xf:]])
    b = out
b = b[:N].copy()
b = set_rms(b, -27.0, clamp=24)

mix = reverb(lead_bus, IR, 0.16) + reverb(choir_bus, IR, 0.5) + b
mix[: int(1.5 * SR)] *= np.linspace(0, 1, int(1.5 * SR))[:, None]
mix[-int(6 * SR):] *= np.linspace(1, 0, int(6 * SR))[:, None]
raw = OUT / "song-raw.wav"
import wave
with wave.open(str(raw), "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes((np.clip(mix / max(1.0, np.abs(mix).max()), -1, 1) * 32767).astype("<i2").tobytes())
final = OUT / "song.mp3"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", "loudnorm=I=-16:TP=-1.5:LRA=9", "-b:a", "192k", str(final)], check=True)

# ---------- continuity stats on the voice bus (lead + choir) ----------
vb = lead_bus + choir_bus
fr = int(0.05 * SR)
e = np.sqrt((vb[: len(vb) // fr * fr].reshape(-1, fr, 2) ** 2).mean(axis=(1, 2)) + 1e-12)
db = 20 * np.log10(e + 1e-12)
quiet = db < -52
longest, run = 0, 0
for q in quiet[int(a.intro / 0.05): int(voice_end / 0.05)]:
    run = run + 1 if q else 0
    longest = max(longest, run)
cuts, prev_end = [], None
for v in range(1, 6):
    prev = [ev for ev in events if ev["line"][0] == v - 1][-1]["choir_end"]
    nxt = verse_first[v]
    cuts.append(round((prev + nxt) / 2, 2))
plan = dict(bed=bed_case, total=round(total, 2), voice_start=a.intro, voice_end=round(voice_end, 2), longest_voice_silence_s=round(longest * 0.05, 2), cuts=cuts, events=events)
json.dump(plan, open(OUT / "plan.json", "w"), indent=1)
log(json.dumps({k: plan[k] for k in ("bed", "total", "voice_start", "voice_end", "longest_voice_silence_s", "cuts")}))
for ev in events:
    log(f"{ev['line']} lead {ev['lead_take']} cov {ev['lead_cov']} | choir {ev['choir_kind']} {ev['choir_take']} cov {ev['choir_cov']} | {ev['lead_start']}-{ev['choir_end']}")
log("wrote", final)
