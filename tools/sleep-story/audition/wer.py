import json, re, sys, difflib
tr = json.load(open(sys.argv[1])); amap = json.load(open(sys.argv[2]))
words = list(tr.values())[0]["words"]
ref_txt = " ".join(json.load(open("aud_text.json"))["segments"])
def norm(s): return re.findall(r"[a-z']+", s.lower().replace("’", "'"))
ref = norm(ref_txt)
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (x != y))
    return d[-1]
for a in amap:
    hyp = norm(" ".join(w["text"] for w in words if a["clip_start"] - 0.3 <= w["start"] <= a["end"] + 0.5))
    sm = difflib.SequenceMatcher(None, ref, hyp)
    diffs = [(" ".join(ref[i1:i2]), " ".join(hyp[j1:j2])) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"]
    print(f"V{a['n']} {a['id']}: WER {100 * ed(ref, hyp) / len(ref):.1f}%  diffs {diffs}")
