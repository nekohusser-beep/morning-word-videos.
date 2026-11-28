# Builds the Neko voice tracks (opening + closing) from the Seed-VC converted clips.
# Per clip: gate the converted voice with the ORIGINAL speech mask (kills murmurs in silence), trim to the planned window,
# level every clip to the same speech RMS (steady voice across clips), short fades, place on the segment timeline.
# Writes /home/claude/ps91/mix/voice_open.wav and voice_close.wav (48 kHz mono float32, pre-chain, pre-gain) + clip stats json.
import sys, json, numpy as np, soundfile as sf
from scipy.signal import resample_poly
from scipy.ndimage import maximum_filter1d, uniform_filter1d
sys.path.insert(0, '/home/claude/ps91/build')
import comp_plan as C

SR_IN = 22050; SR = 48000
TARGET_DB = -24.0           # speech-frame RMS every clip is levelled to (before the voice chain)
SRC = C.SRC; VC = C.VC

def load(p):
    x, sr = sf.read(p, dtype='float32')
    if x.ndim > 1: x = x.mean(1)
    assert sr == SR_IN, (p, sr)
    return x

def frame_db(x, hop=220):  # 10 ms frames
    n = len(x) // hop
    e = np.sqrt((x[:n*hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(e + 1e-9)

def speech_mask(src, pad_ms=70, ramp_ms=25):
    db = frame_db(src)
    ref = np.percentile(db, 97)
    thr = max(ref - 34.0, -62.0)
    m = (db > thr).astype(np.float32)
    k = int(pad_ms / 10) * 2 + 1
    m = maximum_filter1d(m, size=k)                       # dilate by pad_ms each side
    m = uniform_filter1d(m, size=max(3, int(ramp_ms / 10)))  # soften edges
    mm = np.repeat(m, 220)                                 # back to samples
    mm = np.pad(mm, (0, max(0, len(src) - len(mm))), mode='edge')[:len(src)]
    # smooth the staircase at sample level
    mm = uniform_filter1d(mm, size=int(0.012 * SR_IN))
    return mm.astype(np.float32), thr, db > thr

def prep(item):
    key = item['key']; a = item['a']; b = item['b']
    s = load(f'{SRC}/{key}.wav'); v = load(f'{VC}/{key}.wav')
    n = min(len(s), len(v)); s = s[:n]; v = v[:n]
    m, thr, sp = speech_mask(s)
    vm = v * m
    # speech-frame RMS of the converted voice (frames where the ORIGINAL had speech)
    db = frame_db(vm); spn = sp[:len(db)]
    rms_db = 10 * np.log10(np.mean(10 ** (db[spn] / 10)) + 1e-12)
    g = 10 ** ((TARGET_DB - rms_db) / 20)
    vm = vm * g
    i0 = int(round(a * SR_IN)); i1 = int(round(b * SR_IN)); i1 = min(i1, n)
    seg = vm[i0:i1].copy()
    fi = int(0.010 * SR_IN); fo = int(0.040 * SR_IN)
    seg[:fi] *= np.linspace(0, 1, fi, dtype=np.float32)
    seg[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)
    seg48 = resample_poly(seg, 320, 147).astype(np.float32)   # 22050 -> 48000
    return seg48, dict(key=key, rms_db_before=round(float(rms_db), 2), gain_db=round(float(20 * np.log10(g)), 2),
                       peak_after=round(float(np.abs(seg48).max()), 3), thr_db=round(float(thr), 1))

def build(plan, length_s, out):
    buf = np.zeros(int(length_s * SR), dtype=np.float32); stats = []
    for it in plan:
        seg, st = prep(it); p = int(round(it['t'] * SR))
        buf[p:p + len(seg)] += seg[:len(buf) - p]; stats.append(st)
    sf.write(out, buf, SR, subtype='FLOAT')
    return stats

if __name__ == '__main__':
    st = {}
    st['open'] = build(C.OPENP, C.OPEN_END + 1.0, '/home/claude/ps91/mix/voice_open.wav')
    st['close'] = build(C.CLOSEP, C.CLOSE_END + 1.0, '/home/claude/ps91/mix/voice_close.wav')
    json.dump(st, open('/home/claude/ps91/mix/voice_stats.json', 'w'), indent=1)
    for k in ('open', 'close'):
        for s in st[k]: print(k, s)
