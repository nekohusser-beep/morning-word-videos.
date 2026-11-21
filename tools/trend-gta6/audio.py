import numpy as np, soundfile as sf, json, math, subprocess
from scipy import signal
from common import START, AL, ORDER, wt, lend, LEAD
import dark as D, light as LT
SR = 48000; END = 59.0; N = int(SR * END)
rng = np.random.default_rng(3)
def T(n): return np.arange(n) / SR
def lp(x, fc, o=2):
    b, a = signal.butter(o, fc / (SR / 2), 'low'); return signal.lfilter(b, a, x)
def hp(x, fc, o=2):
    b, a = signal.butter(o, fc / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def put(bus, x, t0, g=1.0):
    i = int(t0 * SR)
    if i < 0: x = x[-i:]; i = 0
    n = min(len(x), len(bus) - i)
    if n > 0: bus[i:i + n] += x[:n] * g
def fade(x, a=0.01, r=0.05):
    na, nr = int(a * SR), int(r * SR); y = x.copy()
    if na: y[:na] *= np.linspace(0, 1, na)
    if nr: y[-nr:] *= np.linspace(1, 0, nr)
    return y

# ---------------- voice ----------------
vo = np.zeros(N)
for k in ORDER:
    a, sr = sf.read(f'vo_{k}.wav', dtype='float32')
    a = signal.resample_poly(a, 2, 1)
    put(vo, fade(a.astype(np.float64), 0.005, 0.02), START[k])
vo = hp(vo, 75); vo *= 0.89 / np.max(np.abs(vo))

# ---------------- dark bed ----------------
DE = D.DE
def saw(f, n, harm=9):
    t = T(n); x = np.zeros(n)
    for h in range(1, harm + 1): x += np.sin(2 * np.pi * f * h * t + rng.uniform(0, 6.28)) / h
    return x
nd = int((DE + 0.8) * SR); t = T(nd)
drone = lp(saw(55.0, nd) + saw(55.35, nd) + 0.7 * saw(82.41, nd) + 0.6 * saw(82.0, nd) + 0.5 * saw(110.3, nd), 420, 2)
drone *= (0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * t)) / np.max(np.abs(drone))
eerie = (np.sin(2 * np.pi * 880 * t) + np.sin(2 * np.pi * 932.33 * t) + 0.6 * np.sin(2 * np.pi * 1318.5 * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.19 * t))
denv = np.ones(nd); denv[:int(0.25 * SR)] = np.linspace(0, 1, int(0.25 * SR))
i0, i1 = int(D.tC * SR), int(D.tD * SR); denv[i0:i1] = 0.25          # drop under "Easter egg"
i2 = int((DE - 0.5) * SR); denv[i2:] *= np.linspace(1, 0, nd - i2)
denv = lp(denv, 6, 1)
darkL = np.zeros(N + SR); darkR = np.zeros(N + SR)
put(darkL, drone * denv, 0, 0.30); put(darkR, np.roll(drone, 331) * denv, 0, 0.30)
put(darkL, eerie * denv, 0, 0.016); put(darkR, np.roll(eerie, 977) * denv, 0, 0.016)

def boom(amp=1.0, dur=0.9, f0=95, f1=34):
    n = int(dur * SR); tt = T(n); f = f1 + (f0 - f1) * np.exp(-tt * 9)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 4.2)
    c = lp(rng.normal(0, 1, n), 1800) * np.exp(-tt * 38) * 0.6
    return fade((x + c) * amp, 0.002, 0.08)
def thump(amp):
    n = int(0.3 * SR); tt = T(n); f = 38 + 22 * np.exp(-tt * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 15) * amp
hits = np.zeros(N + SR)
for t0, a in [(0.07, 0.75), (wt('hook', 5) + LEAD, 0.95), (wt('hook', 8) + LEAD, 0.5), (D.tB, 0.55), (wt('money', 3) + LEAD, 0.85), (D.tE, 0.4), (D.tD, 0.5)]:
    put(hits, boom(a), t0)
# heartbeat under the ritual
tb = D.tB + 0.3; k = 0
while tb < D.tDEM - 0.9:
    g = 0.26 + 0.34 * (tb - D.tB) / (D.tDEM - D.tB)
    put(hits, thump(g), tb); put(hits, thump(g * 0.7), tb + 0.24); tb += 0.98 - 0.02 * k; k += 1
# riser into the demon line
nr = int(1.5 * SR); tt = T(nr); p = tt / tt[-1]
nz = rng.normal(0, 1, nr); ris = np.zeros(nr)
for fc0, fc1 in [(300, 5200)]:
    seg = 2048
    for s in range(0, nr, seg):
        fc = fc0 * (fc1 / fc0) ** (s / nr); sos = signal.butter(2, [fc * 0.7 / (SR / 2), min(0.99, fc * 1.4 / (SR / 2))], 'band', output='sos')
        ris[s:s + seg] = signal.sosfilt(sos, nz[s:s + seg])
ris = ris * p ** 2.2 * 0.55 + np.sin(2 * np.pi * np.cumsum(110 * 2 ** (2 * p)) / SR) * p ** 2 * 0.22
put(hits, fade(ris, 0.05, 0.01), D.tDEM - 1.5)
# demon hit: big boom + growl + noise
put(hits, boom(1.25, 1.6, 120, 28), D.tDEM)
ng = int(1.55 * SR); tt = T(ng)
growl = lp(saw(41.2, ng, 14) * (0.55 + 0.45 * signal.square(2 * np.pi * 27 * tt)), 420, 2) * np.exp(-tt * 1.3)
put(hits, fade(growl / np.max(np.abs(growl)) * 0.55, 0.01, 0.2), D.tDEM + 0.02)
put(hits, fade(hp(rng.normal(0, 1, int(0.5 * SR)), 2500) * np.exp(-T(int(0.5 * SR)) * 9) * 0.22, 0.002, 0.05), D.tDEM)
# count-up ticks
tk = D.T379 + LEAD; gap = 0.11
while tk < D.T379 + 1.25:
    n = int(0.012 * SR); put(hits, hp(rng.normal(0, 1, n), 3000) * np.exp(-T(n) * 600) * 0.20, tk); tk += gap; gap = max(0.035, gap * 0.9)
# whoosh into the light
nw = int(1.1 * SR); tt = T(nw); w = lp(rng.normal(0, 1, nw), 900) * np.sin(np.pi * tt / tt[-1]) ** 2 * 0.5
put(hits, w, DE - 0.75)

# ---------------- light bed ----------------
def pad_note(f, n, seed):
    r = np.random.default_rng(seed); tt = T(n); x = np.zeros(n)
    for det in (-0.35, 0.0, 0.4):
        ff = f * 2 ** (det / 100)
        x += np.sin(2 * np.pi * ff * tt + r.uniform(0, 6.28)) + 0.32 * np.sin(2 * np.pi * 2 * ff * tt + r.uniform(0, 6.28)) + 0.12 * np.sin(2 * np.pi * 3 * ff * tt + r.uniform(0, 6.28))
    return x * (0.8 + 0.2 * np.sin(2 * np.pi * r.uniform(0.08, 0.2) * tt + r.uniform(0, 6.28)))
def chord(freqs, t0, t1, seed, xf=0.9):
    n = int((t1 - t0 + 2 * xf) * SR); L = np.zeros(n); R = np.zeros(n)
    for j, f in enumerate(freqs):
        g = 1.0 / (1 + 0.45 * j)
        L += pad_note(f, n, seed + j) * g; R += pad_note(f, n, seed + 50 + j) * g
    e = np.ones(n); m = int(2 * xf * SR); e[:m] = np.sin(np.linspace(0, np.pi / 2, m)) ** 2; e[-m:] = np.cos(np.linspace(0, np.pi / 2, m)) ** 2
    return L * e, R * e, t0 - xf
padL = np.zeros(N + 4 * SR); padR = np.zeros(N + 4 * SR)
LS = LT.LS
for fr, a, b, sd in [([146.83, 220.0, 293.66, 369.99], LS, LT.tG, 1), ([123.47, 185.0, 246.94, 293.66], LT.tG, LT.tH, 2),
                     ([98.0, 146.83, 196.0, 246.94, 293.66], LT.tH, LT.tI, 3), ([146.83, 220.0, 293.66, 369.99, 440.0, 587.33], LT.tI, END + 1.0, 4)]:
    l, r, t0 = chord(fr, a, b, sd); put(padL, l, t0 + 0.2); put(padR, r, t0 + 0.2)
padL = lp(padL, 1700); padR = lp(padR, 1700)
def bell(f, amp=1.0, dur=3.0):
    n = int(dur * SR); tt = T(n)
    x = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 2.2) + 0.35 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 5) + 0.2 * np.sin(2 * np.pi * f * 2 * tt) * np.exp(-tt * 3)
    return fade(x * amp, 0.004, 0.2)
bells = np.zeros(N + 4 * SR)
for t0, fs_ in [(wt('psalm', 11) + LEAD, [880.0]), (wt('eph', 16) + LEAD, [739.99]), (wt('prayer', 11) + LEAD, [587.33, 880.0]), (wt('ask', 1) + LEAD, [587.33, 880.0, 1174.66])]:
    for j, f in enumerate(fs_): put(bells, bell(f, 0.5 / (1 + 0.5 * j)), t0 + 0.03 * j)
# reverb for pad + bells
ir = rng.normal(0, 1, int(2.2 * SR)) * np.exp(-T(int(2.2 * SR)) * 2.6); ir = lp(ir, 4500); ir /= np.sqrt(np.sum(ir ** 2))
bw = signal.fftconvolve(bells, ir)[:len(bells)]

def rms(x): return float(np.sqrt(np.mean(x ** 2) + 1e-12))
sp = np.abs(vo) > 0.02; rv = rms(vo[sp])
iD = int(DE * SR)
bedD_L = darkL[:N]; bedD_R = darkR[:N]
gD = rv * 10 ** (-15.5 / 20) / rms(bedD_L[int(8 * SR):int(16 * SR)])
bedP_L = padL[:N] + (bells[:N] * 1.6 + bw[:N] * 1.5); bedP_R = padR[:N] + (bells[:N] * 1.6 + np.roll(bw, 700)[:N] * 1.5)
gP = rv * 10 ** (-17.0 / 20) / rms(padL[int(38 * SR):int(48 * SR)])
hk = 0.80 * np.max(np.abs(vo)) / np.max(np.abs(hits[:N]))
print('rms vo', round(rv, 3), 'gD', round(gD, 3), 'gP', round(gP, 4), 'hk', round(hk, 3))
L = bedD_L * gD + hits[:N] * hk + bedP_L * gP; R = bedD_R * gD + hits[:N] * hk + bedP_R * gP
envv = lp(np.abs(vo), 6, 1); duck = 1 - 0.36 * np.clip(envv / 0.12, 0, 1)
L = L * duck + vo; R = R * duck + vo
fo = int(0.9 * SR); L[-fo:] *= np.linspace(1, 0, fo); R[-fo:] *= np.linspace(1, 0, fo)
pk = max(np.max(np.abs(L)), np.max(np.abs(R))); print('peak', round(pk, 3))
st = np.stack([L, R], 1) / max(1.0, pk / 0.97)
sf.write('mix_raw.wav', st.astype(np.float32), SR)
import re
o = subprocess.run(['ffmpeg', '-hide_banner', '-i', 'mix_raw.wav', '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1]); g = -14.0 - I; print('I', I, 'gain', round(g, 2))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'mix_raw.wav', '-af', f'volume={g:.2f}dB,alimiter=limit=0.78:level=false:attack=3:release=60', '-ar', '48000', 'mix.wav'], check=True)
print('audio ok', N / SR)
