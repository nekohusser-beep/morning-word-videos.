"""voice-lab scorer. Speaker match (ECAPA cosine) of every candidate vs real Derrick blocks, pitch, word-exact check, and one demo mp3.
Real blocks b4/b5/b8 were NOT used in vl/ref.wav. Baseline = how far real Derrick blocks sit from each other."""
import os, re, json, glob, difflib, itertools, subprocess
import numpy as np, soundfile as sf, torch, torchaudio
import torch.nn.functional as F
import parselmouth
from speechbrain.inference.speaker import EncoderClassifier
from faster_whisper import WhisperModel

clf = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="pretrained_ecapa", run_opts={"device": "cpu"})


def load16(p):
    x, sr = sf.read(p, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    if sr != 16000:
        x = torchaudio.functional.resample(torch.tensor(x), sr, 16000).numpy()
    return x


def emb(x):
    with torch.no_grad():
        e = clf.encode_batch(torch.tensor(x).unsqueeze(0)).squeeze()
    return F.normalize(e, dim=0)


def f0(x):
    s = parselmouth.Sound(x.astype(np.float64), sampling_frequency=16000)
    v = s.to_pitch(time_step=0.01, pitch_floor=70, pitch_ceiling=300).selected_array["frequency"]
    v = v[v > 0]
    return round(float(np.median(v)), 1), round(float(np.percentile(v, 10)), 1), round(float(np.percentile(v, 90)), 1)


def words(t):
    t = t.lower().replace("-", " ")
    return [w for w in re.sub(r"[^a-z0-9' ]", " ", t).split() if w]


real = {"b4": "vl/held/b4.wav", "b5": "vl/held/b5.wav", "b8": "vl/held/b8.wav", "ref": "vl/ref.wav"}
E = {k: emb(load16(p)) for k, p in real.items()}
base = {f"{a}-{b}": round(float(E[a] @ E[b]), 3) for a, b in itertools.combinations(["b4", "b5", "b8"], 2)}
base.update({f"ref-{b}": round(float(E["ref"] @ E[b]), 3) for b in ("b4", "b5", "b8")})
print("REAL vs REAL", base, flush=True)

NAMES = {"K": "Kokoro am_onyx raw (floor)", "C": "Chatterbox clone of ref (direct)", "V_K": "Kokoro -> Seed-VC -> Derrick", "V_C": "Chatterbox -> Seed-VC -> Derrick"}
paras = [p.strip() for p in open("vl/lines.txt").read().split("\n\n") if p.strip()]
wh = WhisperModel("medium.en", device="cpu", compute_type="int8")
rows = []
for fp in sorted(glob.glob("in/*.wav")):
    nm = os.path.basename(fp)[:-4]
    m = re.match(r"(V_[KC]|[KC])_(\d+)$", nm)
    if not m:
        continue
    fam, n = m.group(1), int(m.group(2))
    x = load16(fp)
    e = emb(x)
    sims = {k: round(float(e @ E[k]), 3) for k in ("b4", "b5", "b8")}
    segs, _ = wh.transcribe(fp, vad_filter=False)
    got = words(" ".join(s.text for s in segs))
    want = words(paras[n - 1])
    sm = difflib.SequenceMatcher(None, want, got)
    diffs = [(op, " ".join(want[a:b]), " ".join(got[c:d])) for op, a, b, c, d in sm.get_opcodes() if op != "equal"]
    rows.append({"clip": nm, "what": NAMES.get(fam, fam), "secs": round(len(x) / 16000, 2), "match_vs_real": sims,
                 "match_avg": round(float(np.mean(list(sims.values()))), 3), "f0_med_p10_p90": f0(x),
                 "word_ratio": round(sm.ratio(), 3), "word_diffs": diffs[:8]})
    print(rows[-1], flush=True)

pitch_real = {k: f0(load16(p)) for k, p in real.items()}
json.dump({"real_vs_real": base, "real_f0": pitch_real, "candidates": rows}, open("metrics.json", "w"), indent=1)

# demo: same words (block 4 text) in order real, then each free candidate, loudness-matched, 1.4 s apart
order = ["vl/held/b4.wav", "in/V_K_1.wav", "in/V_C_1.wav", "in/C_1.wav"]
parts = []
for i, p in enumerate(order):
    if not os.path.exists(p):
        continue
    o = f"demo_{i}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100,pan=mono|c0=c0", "-c:a", "pcm_s16le", o], check=True)
    parts.append(o)
if parts:
    sil = "gap.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "1.4", sil], check=True)
    lst = []
    for p in parts:
        lst += [p, sil]
    open("list.txt", "w").write("".join(f"file '{p}'\n" for p in lst[:-1]))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c:a", "libmp3lame", "-b:a", "128k", "voice-test-block4.mp3"], check=True)
    print("demo parts:", parts)
