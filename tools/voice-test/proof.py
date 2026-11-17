"""Word-proof the test clips: transcribe each wav with faster-whisper (small.en, CPU, int8) and diff it word for word against Psalm 23:1-3 KJV.
Whisper proves WORDS, not taste (Neko picks the voice by ear). Writes out/PROOF.json and prints every mismatch."""
import glob, json, os, re, sys, time
from faster_whisper import WhisperModel

EXPECTED = ("The Lord is my shepherd; I shall not want. "
            "He maketh me to lie down in green pastures: he leadeth me beside the still waters. "
            "He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake.")

def norm(t):
    t = t.lower().replace("’", "'")
    t = re.sub(r"[^a-z' ]+", " ", t)
    return t.split()

def edit_ops(ref, hyp):
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): d[i][0] = i
    for j in range(m + 1): d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + (ref[i-1] != hyp[j-1]))
    i, j, ops = n, m, []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i-1][j-1] + (ref[i-1] != hyp[j-1]):
            if ref[i-1] != hyp[j-1]: ops.append(("sub", ref[i-1], hyp[j-1]))
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i-1][j] + 1:
            ops.append(("miss", ref[i-1], "")); i -= 1
        else:
            ops.append(("extra", "", hyp[j-1])); j -= 1
    return d[n][m], ops[::-1]

ref = norm(EXPECTED)
model = WhisperModel("small.en", device="cpu", compute_type="int8")
res = {}
for f in sorted(glob.glob("wavs/*.wav")):
    t0 = time.time()
    segs, _ = model.transcribe(f, language="en", beam_size=5, vad_filter=False)
    text = " ".join(s.text.strip() for s in segs)
    hyp = norm(text)
    dist, ops = edit_ops(ref, hyp)
    res[os.path.basename(f)] = {"heard": text, "wer_pct": round(100 * dist / len(ref), 1), "errors": ops, "secs": round(time.time() - t0, 1)}
    print(os.path.basename(f), "WER", res[os.path.basename(f)]["wer_pct"], "%", "|", text, "|", ops, flush=True)
os.makedirs("out", exist_ok=True)
json.dump(res, open("out/PROOF.json", "w"), indent=1)
