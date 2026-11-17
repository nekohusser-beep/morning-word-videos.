"""cutplan.py: choose every camera-to-camera cut on open eyes (Neko's Day 1 rule: never cut on a closed-eye or head-down frame).
Eye openness (eyes.py) is the share of bright, low-saturation (sclera) pixels in the eye boxes. A frame counts as CLOSED when it is under an
absolute floor (EYE_ABS 0.045) or well under its own surroundings (below 80% of the median of the +-0.5 s around it): a full blink on a wide-eyed
clip only drops to about 0.057, so a fixed threshold misses it.
For each cut A->B it searches how far before B's first word to cut: B must be open for 0.12 s after the cut, A open for 0.12 s before it. When A is
closed at the default position it holds A's last open frame instead (A's 'last good frame').
Writes cutplan.json {"back": {B: seconds before B's onset}, "ge": {A: clip time of the last open frame}}."""
import json, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eyes
W = os.path.dirname(os.path.abspath(__file__)); OPEN = 5.7333; ABS = float(os.environ.get("EYE_ABS", "0.045")); REL = 0.80
CLIP = json.load(open(f"{W}/clipmap.json")); VIS_CAM = [str(i) for i in range(1, 16) if str(i) != "9"]
T = {}; t = OPEN + 0.30
for k in [str(i) for i in range(1, 16)]:
    c, s, e, ge, gap = CLIP[k][:5]; T[k] = t; t += (e - s) + gap
S = {}
for k in VIS_CAM:
    ser = eyes.series(f"{W}/clips/{CLIP[k][0]}.mp4"); ts = np.array([a for a, b in ser]); v = np.array([b for a, b in ser])
    med = np.array([np.median(v[max(0, i - 15):i + 16]) for i in range(len(v))])
    S[k] = (ts, v, (v >= ABS) & (v >= REL * med))          # open flag per frame
def ok(k, x, w):
    """True when every frame in [x, x+w] (w<0: [x+w, x]) is open"""
    ts, v, o = S[k]; lo, hi = (x, x + w) if w >= 0 else (x + w, x)
    m = (ts >= lo - 0.02) & (ts <= hi + 0.02)
    return bool(o[m].all()) if m.any() else bool(o[int(np.argmin(abs(ts - x)))])
plan = {"back": {}, "ge": {}}; log = []
for ka, kb in [(a, b) for a, b in zip(VIS_CAM, VIS_CAM[1:]) if int(b) == int(a) + 1]:
    cA, sA, eA, geA, gapA = CLIP[ka][:5]; sB = CLIP[kb][1]
    gap = T[kb] - (T[ka] + (eA - sA))
    d0 = min(max(sB - 0.02, 0.03), gap * 0.5)
    cands = sorted({round(x / 30, 4) for x in range(1, int(gap * 0.85 * 30) + 1)}, key=lambda x: abs(x - d0))
    pick = None
    for back in cands:
        x0 = sB - back                                   # B's clip time at the cut (negative: B's first frame is held before it)
        if not ok(kb, max(0.0, x0), max(0.0, 0.12 + min(0.0, x0))): continue
        tA = sA + (T[kb] - back - T[ka])
        if ok(ka, min(tA, geA if geA else 9.9), -0.12): pick = (back, None); break
        tsA, vA, oA = S[ka]                              # A closed at the cut: hold A's last frame that has open eyes behind it
        idx = [i for i in range(len(tsA)) if tsA[i] <= tA - 0.02 and oA[max(0, i - 3):i + 1].all()]
        if idx and tA - tsA[idx[-1]] <= 1.2: pick = (back, float(tsA[idx[-1]])); break
    if pick is None: log.append(f"L{ka}->L{kb}: NO open-eye cut found, keeping default"); continue
    back, ge = pick; plan["back"][kb] = round(back, 4)
    if ge is not None: plan["ge"][ka] = round(ge, 3)
    log.append(f"L{ka}->L{kb}: cut {back:.3f}s before L{kb} onset (default {d0:.3f})" + (f"; L{ka} held from clip {ge:.2f}" if ge is not None else ""))
# The eye boxes are fixed for a locked camera; on lines where he opens with his head lifted and eyes lowered (L6, L12, L15) they read open
# while the frame shows a blink, so those three cuts were set by eye from frame strips of the incoming clip (Nov 5):
# L6 clip c06 open until 0.60 (blink 0.65-0.75), L12 clip c12 open until 0.10 (blink 0.15-0.35), L15 clip c15 open until 0.30 (blink 0.35-0.50).
MANUAL = {"6": 0.36, "12": 0.38, "15": 0.50}
for kb, b in MANUAL.items(): plan["back"][kb] = b; log.append(f"L{kb}: cut {b:.2f}s before onset (set by eye from the frame strip)")
print("\n".join(log)); json.dump(plan, open(f"{W}/cutplan.json", "w"), indent=1)
