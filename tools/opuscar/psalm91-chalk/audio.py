"""Sound for Psalm 91 (Chalkboard) -> mix.wav (48 kHz stereo, exactly DUR seconds).
Run from the library root:  node core/render/events.mjs films/psalm91-chalk ; .venv/bin/python films/psalm91-chalk/audio.py
Voice: Kokoro am_michael (vo/*.wav), the loudest thing in the mix. Chalk: synthesized grains (foley/lib), one chain per stroke.
Score: a plucked nylon string (Karplus-Strong), a soft marimba-like sine bell and a low pizzicato, D major, sparse; silent under the verdict."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); LIB = os.path.abspath(os.path.join(HERE, '../..'))
sys.path.insert(0, LIB)
import numpy as np, soundfile as sf, soxr
from core.audio.sfx import SR, add, limit, noise, bp, hp, lp, t_, brown

rng = np.random.default_rng(7)
EV = json.load(open(os.path.join(HERE, 'events.json')))
DUR = EV['dur']; ev = EV['ev']; N = int(round(DUR * SR))
vo = {e['id']: e['t'] for e in ev if e['type'] == 'vo'}
voice, fx, mus = (np.zeros((N, 2), np.float32) for _ in range(3))

def fade(x, a=.004, b=.03):
    n = len(x); a, b = min(int(a * SR), n // 2), min(int(b * SR), n // 2)
    x = x.copy(); x[:a] *= np.linspace(0, 1, a); x[n - b:] *= np.linspace(1, 0, b); return x

# ---------------------------------------------------------------- voice
VO_END = 0
for vid, t in vo.items():
    x, sr = sf.read(os.path.join(HERE, 'vo', vid + '.wav'), dtype='float32')
    if x.ndim > 1: x = x.mean(1)
    x = soxr.resample(x, sr, SR); x = hp(x, 90).astype(np.float32)
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * .085
    add(voice, x, t, 1.0, 0); VO_END = max(VO_END, t + len(x) / SR)
vpres = np.abs(voice[:, 0]); k = int(.25 * SR)
vpres = np.convolve(vpres, np.ones(k) / k, 'same'); vpres = np.clip(vpres / (vpres.max() + 1e-9) * 3, 0, 1)

# ---------------------------------------------------------------- chalk
IDX = json.load(open(os.path.join(HERE, 'foley/lib/index.json')))
strokes = [g for g in IDX if g['kind'] == 'stroke']; taps = [g for g in IDX if g['kind'] == 'tap']
cache = {}
def grain(g):
    if g['file'] not in cache:
        x, sr = sf.read(os.path.join(HERE, 'foley/lib', g['file']), dtype='float32')
        if x.ndim > 1: x = x.mean(1)
        if sr != SR: x = soxr.resample(x, sr, SR)
        cache[g['file']] = x / (np.abs(x).max() + 1e-9)
    return cache[g['file']]
def chalk(d, orange=False):
    out = np.zeros(int((d + .06) * SR), np.float32); pos = 0
    while pos < len(out) - int(.03 * SR):
        g = grain(strokes[rng.integers(len(strokes))]); n = min(len(g), len(out) - pos)
        out[pos:pos + n] += fade(g[:n], .006, .02); pos += max(int(.6 * n), int(.04 * SR))
    env = np.ones(len(out)); a = int(.012 * SR); env[:a] = np.linspace(.3, 1, a); env[-int(.05 * SR):] *= np.linspace(1, 0, int(.05 * SR))
    out = out * env
    out = lp(out, 3800) if orange else hp(out, 500)
    return (out / (np.abs(out).max() + 1e-9)).astype(np.float32)
for e in ev:
    if e['type'] != 'chalk': continue
    d = max(.04, e['d']); lvl = (.012 + .02 * min(1, e['len'] / 400)) * (1.25 if e.get('big') else 1)
    add(fx, chalk(d, e['color'] == 'orange'), e['t'], lvl, e['pan'])
    if e['len'] > 60 and rng.random() < .6:   # a light knock as the chalk lands
        g = grain(taps[rng.integers(len(taps))]); add(fx, g, e['t'] - .005, .006, e['pan'])
# the wipe: a felt pass; the panel: a low roll ending on a stop
for e in ev:
    if e['type'] == 'wipe':
        d = e['d'] + .25; x = bp(noise(d), 300, 1800) * np.hanning(int(round(d * SR)))
        add(fx, (x / (np.abs(x).max() + 1e-9)).astype(np.float32), e['t'] - .05, .05, .3)
    elif e['type'] == 'slide':
        d = e['d'] + .3; n = int(round(d * SR)); tt = np.arange(n) / SR
        x = lp(brown(d), 420) * (1 - np.exp(-tt / .08)) * np.exp(-((tt - d * .5) / (d * .45)) ** 2)
        stop = bp(noise(.08), 80, 600) * np.exp(-np.arange(int(.08 * SR)) / SR / .02)
        x = x / (np.abs(x).max() + 1e-9); add(fx, x.astype(np.float32), e['t'], .16, 0); add(fx, (stop / (np.abs(stop).max() + 1e-9)).astype(np.float32), e['t'] + e['d'], .12, 0)

# ---------------------------------------------------------------- score: Karplus-Strong nylon, sine bell, pizz bass
def ks(f, d, bright=.5, v=1.0):
    n = int(d * SR); L = int(SR / f); buf = (rng.random(L) * 2 - 1); buf = lp(buf, 2000 + 6000 * bright)
    out = np.zeros(n, np.float32); y1 = 0.0; a = .5 * (1 - .02 * (1 - bright))
    for i in range(n):
        j = i % L; y = buf[j]; out[i] = y; buf[j] = a * (y + y1) * .996; y1 = y
    out *= np.exp(-np.arange(n) / SR / (d * .6)); return out * v
def bell(f, d, v=1.0):
    tt = t_(d); x = np.sin(2 * np.pi * f * tt) * np.exp(-tt / (d * .35)) + .25 * np.sin(2 * np.pi * f * 3.98 * tt) * np.exp(-tt / (d * .12))
    return (x * v * .6).astype(np.float32)
def pizz(f, d, v=1.0):
    return lp(ks(f, d, .15, v), 900).astype(np.float32)
NOTE = lambda n: 440 * 2 ** ((n - 69) / 12)
D4, E4, Fs4, A4, B4, D5, E5, Fs5, A5 = (NOTE(n) for n in (62, 64, 66, 69, 71, 74, 76, 78, 81))
D2, A2, B2, G2 = (NOTE(n) for n in (38, 45, 47, 43))
score = np.zeros((N, 2), np.float32)
# a few plucks born from the writing: at the first title stroke, then one per verse's first keyword, in the pauses between lines
title_t = next(e['t'] for e in ev if e['type'] == 'title')
seq = [(title_t + .1, A4, 2.4, .5), (title_t + .9, D5, 2.4, .42), (title_t + 1.5, Fs5, 2.8, .36)]
line_starts = sorted(vo.values())
for i, t in enumerate(line_starts):
    # a short figure in the gap before each line
    seq += [(t - 1.1, D4, 2.0, .4), (t - .75, Fs4, 2.0, .34), (t - .4, A4, 2.4, .3)]
    if i % 2 == 1: seq.append((t - .4, D5, 2.2, .22))
for t, f, d, v in seq:
    if 0 <= t < DUR - .2: add(score, ks(f, d, .55, v), t, 1.0, (rng.random() - .5) * .4)
# bells on the verdict words (orange chalk) and the end card
for e in ev:
    if e['type'] == 'chalk' and e['color'] == 'orange' and e['t'] > 0:
        pass
for e in ev:
    if e['type'] == 'endcard': add(score, bell(D5, 4.0, .5), e['t'] + .3, 1.0, 0); add(score, bell(A5, 4.5, .3), e['t'] + 1.1, 1.0, .2); add(score, pizz(D2, 3.0, .6), e['t'] + .3, 1.0, 0)
# a slow pizzicato bass under the back board (verses 11 and 15), every 3 seconds
bk0 = next((e['t'] for e in ev if e['type'] == 'slide'), 0)
t = bk0 + .6; k = 0
while t < VO_END + 1.5:
    add(score, pizz([D2, A2, B2, G2][k % 4], 2.6, .55), t, 1.0, 0); t += 3.0; k += 1
mus = score
# the score ducks under the voice (voice first) and goes quiet under the last verse's verdict
duck = 1 - .72 * vpres
dk = int(.12 * SR); duck = np.convolve(duck, np.ones(dk) / dk, 'same')
mus = mus * duck[:, None].astype(np.float32)

# ---------------------------------------------------------------- room tone, mix
room = (lp(brown(DUR), 300) * .012).astype(np.float32)
amb = np.stack([room, np.roll(room, 211)], 1)
mix = voice * 1.0 + fx * .9 + mus * .28 + amb
mix[:int(.3 * SR)] *= np.linspace(0, 1, int(.3 * SR))[:, None]
mix = np.stack([limit(mix[:, 0], .95), limit(mix[:, 1], .95)], 1)
sf.write(os.path.join(HERE, 'mix.wav'), mix.astype(np.float32), SR)
print('mix.wav', round(DUR, 2), 's')
