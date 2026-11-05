"""QC of locked-voice unit wavs: Whisper word check vs the unit text, and median pitch vs the reference clip."""
import sys, re, json, glob
import numpy as np, parselmouth
from faster_whisper import WhisperModel
units = {u["idx"]: u["text"].replace("LORD", "Lord") for u in json.load(open(sys.argv[1]))}
ref = sys.argv[2]
def f0(path):
    p = parselmouth.Sound(path).to_pitch(pitch_floor=70, pitch_ceiling=400).selected_array["frequency"]
    p = p[p > 0]
    return float(np.median(p)), float(12 * np.log2(np.percentile(p, 90) / np.percentile(p, 10)))
norm = lambda s: re.sub(r"[^a-z ]", "", s.lower().replace("-", " ")).split()
def wer(w, g):
    d = [[0] * (len(g) + 1) for _ in range(len(w) + 1)]
    for i in range(len(w) + 1): d[i][0] = i
    for j in range(len(g) + 1): d[0][j] = j
    for i in range(1, len(w) + 1):
        for j in range(1, len(g) + 1):
            d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + (w[i-1] != g[j-1]))
    return d[len(w)][len(g)]
m = WhisperModel("medium.en", device="cpu", compute_type="int8")
rf = f0(ref)
print(f"REF median F0 {rf[0]:.0f} Hz, p10-p90 {rf[1]:.1f} semitones")
for path in sorted(glob.glob("out/u*.wav")):
    idx = int(re.search(r"u(\d+)\.wav", path).group(1))
    segs, _ = m.transcribe(path, language="en", beam_size=5)
    got = " ".join(s.text for s in segs)
    w = norm(units[idx]); e = wer(w, norm(got))
    f = f0(path)
    print(f"u{idx:03d} median F0 {f[0]:.0f} Hz ({(f[0]/rf[0]-1)*100:+.0f}% vs ref), range {f[1]:.1f} st, word errors {e}/{len(w)}")
    print("   HEARD:", got.strip())
