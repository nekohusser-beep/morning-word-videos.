import json, os, sys, numpy as np, soundfile as sf
book = json.load(open(sys.argv[1])); d = sys.argv[2]
chs = {int(c["chapter"]): c for c in book["chapters"]}
rows = []; clip = {}
for f in sorted(os.listdir(d)):
    n = int(f[:3]); a, sr = sf.read(os.path.join(d, f), dtype="float32")
    clip[f] = int((np.abs(a) >= 0.999).sum())
    if n == 0: continue
    # 20 ms frame energy, find speech islands separated by >= 2.0 s of quiet
    hop = int(sr * 0.02); fr = len(a) // hop
    e = np.sqrt((a[:fr * hop].reshape(fr, hop) ** 2).mean(1)) > 10 ** (-45 / 20)
    segs = []; start = None; quiet = 0
    for i, v in enumerate(e):
        if v:
            if start is None: start = i
            quiet = 0; end = i
        elif start is not None:
            quiet += 1
            if quiet >= 100: segs.append((start, end)); start = None
    if start is not None: segs.append((start, end))
    verses = chs[n]["verses"]
    rows.append((f, len(segs), len(verses) + 1, [(s * 0.02, (e2 - s) * 0.02) for s, e2 in segs], [len(v["text"].split()) for v in verses]))
bad = []; rates = []
for f, ns, nv, segs, wc in rows:
    if ns != nv: bad.append((f, f"segments {ns} vs expected {nv}")); continue
    for k, ((t, dur), w) in enumerate(zip(segs[1:], wc), 1):
        rates.append(dur / w)
med = float(np.median(rates))
for f, ns, nv, segs, wc in rows:
    if ns != nv: continue
    for k, ((t, dur), w) in enumerate(zip(segs[1:], wc), 1):
        r = dur / w / med
        if r < 0.6 or r > 1.8: bad.append((f, f"verse {k}: {w} words in {dur:.1f}s ({r:.2f}x normal) at {t:.0f}s"))
print("median sec/word", round(med, 3))
print("files with clipped samples:", sum(1 for v in clip.values() if v), "max", max(clip.values()), "total", sum(clip.values()))
print("flags:", len(bad))
for b in bad[:60]: print(" ", *b)
