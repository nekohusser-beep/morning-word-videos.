# Word-exact check: transcribe the finished file's audio and compare to script.txt
import sys, re, json, difflib
from faster_whisper import WhisperModel
def norm(t):
    t = t.lower().replace("’", "'")
    t = re.sub(r"[^a-z0-9' ]+", " ", t)
    return t.split()
ref = norm(open("script.txt", encoding="utf-8").read())
m = WhisperModel("small.en", device="cpu", compute_type="int8")
res = {}
for f in sys.argv[1:]:
    segs, _ = m.transcribe(f, language="en", beam_size=5)
    hyp_text = " ".join(s.text for s in segs)
    hyp = norm(hyp_text)
    sm = difflib.SequenceMatcher(a=ref, b=hyp)
    errs = []
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op != "equal":
            errs.append({"op": op, "script": " ".join(ref[a1:a2]), "heard": " ".join(hyp[b1:b2])})
    wer = sum(max(a2 - a1, b2 - b1) for op, a1, a2, b1, b2 in sm.get_opcodes() if op != "equal") / max(1, len(ref))
    res[f] = {"words_script": len(ref), "words_heard": len(hyp), "wer": round(wer, 4), "diffs": errs, "heard": hyp_text.strip()}
    print("CHECK", f, "WER", round(wer, 4), "diffs", errs)
json.dump(res, open("check.json", "w"), indent=1)
