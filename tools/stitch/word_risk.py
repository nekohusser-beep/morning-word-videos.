#!/usr/bin/env python3
"""word_risk.py - pronunciation guard for Derrick/Naomi scripts (free, local, no credits).
Root cause it closes: a rare word ('supplication') reached the paid Hailuo render with no check, and the
word-diff afterwards was too tolerant to catch the bad read. Run BEFORE any credits, then AFTER each clip.

  python3 word_risk.py scan  script.txt            list unproven risky words (exit 1 if any)
  python3 word_risk.py check script.txt tr.json    strict post-clip check; on pass, proven words go in the ledger
  python3 word_risk.py compare a.json b.json       two Whisper models (medium.en vs large-v3) must agree word for word
  python3 word_risk.py seed  tr1.json tr2.json ... add words Whisper heard right to the ledger

Needs: pip install wordfreq. Ledger: word_ledger.json next to this file."""
import json, re, sys, os
from wordfreq import zipf_frequency as zf
LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'word_ledger.json')
RARE = 3.0      # zipf below this = risky (supplication 2.5, beseech 2.7, therewith 2.5, preserveth 0.0)
def load():
    try: return json.load(open(LEDGER))
    except Exception: return {}
def save(l): json.dump(l, open(LEDGER, 'w'), indent=1, sort_keys=True)
def spoken(text):
    """Only what Derrick says: text after the colon on 'B1 FACE (...):' lines; a plain script is taken whole."""
    lines = [m.group(1) for m in re.finditer(r'^B\d+\b[^:\n]*:\s*(.+)$', text, re.M)]
    return '\n'.join(lines) if lines else text
def words(text):
    text = re.sub(r'[#*_`>\[\]()]', ' ', text)
    return [(m.group(0).lower().strip("'"), m.start()) for m in re.finditer(r"[A-Za-z][A-Za-z']*", text)]
def risky(w): return zf(w, 'en') < RARE
def ctx(text, pos):
    a = text.rfind('\n', 0, pos) + 1; b = text.find('\n', pos); b = len(text) if b < 0 else b
    return text[a:b].strip()[:110]
def scan(path):
    text = spoken(open(path).read()); led = load(); seen = {}; bad = 0
    for w, pos in words(text):
        if not risky(w) or w in seen: continue
        seen[w] = 1; st = led.get(w, {})
        if st.get('status') == 'ok': continue
        bad += 1
        tag = 'KNOWN-BAD' if st.get('status') == 'bad' else 'UNPROVEN'
        print(f"{tag:9} {w:16} zipf {zf(w,'en'):.1f}  | {ctx(text,pos)}")
        if st.get('note'): print(f"          note: {st['note']}")
    if bad: print(f"\n{bad} word(s) need a plan BEFORE credits: swap for a plain word (non-scripture lines), or respell in the prompt "
                  "(sup-pli-kay-shun style, scripture lines) AND generate that block FIRST, check it, then spend on the rest.")
    else: print("clean: no unproven risky words")
    return bad
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "x x twenty thirty forty fifty sixty seventy eighty ninety".split()
def n2w(n):
    if n < 20: return [ONES[n]]
    if n < 100: return [TENS[n // 10]] + ([ONES[n % 10]] if n % 10 else [])
    return [ONES[n // 100], 'hundred'] + (n2w(n % 100) if n % 100 else [])
def norm(raw):
    """lowercase word list; digits spelled out; spelling aliases (derek->derrick) from the ledger."""
    al = load().get('__alias__', {}); out = []
    for t in raw:
        for part in re.findall(r"\d+|[A-Za-z][A-Za-z']*", t):
            if part.isdigit(): out += n2w(int(part)) if int(part) < 1000 else [part]
            else:
                part = part.lower().strip("'"); out.append(al.get(part, part))
    return out
def diffs(ref, hyp, label):
    from difflib import SequenceMatcher
    bad = 0
    for op, a0, a1, b0, b1 in SequenceMatcher(None, ref, hyp, autojunk=False).get_opcodes():
        if op == 'equal': continue
        bad += 1
        print(f"DIFF  {label}: expected '{' '.join(ref[max(0,a0-3):a0])} [{' '.join(ref[a0:a1])}] {' '.join(ref[a1:a1+2])}'  heard '[{' '.join(hyp[b0:b1])}]'")
    return bad
def tokens(tr):
    out = []
    for v in tr.values():
        out += [re.sub(r"[^a-z']", '', x['text'].lower()) for x in v['words']]
    return [t for t in out if t]
def check(path, trpath):
    text = spoken(open(path).read()); led = load(); tr = tokens(json.load(open(trpath))); heard = set(tr)
    script = {w for w, _ in words(text)}; fails = 0
    blocks = [norm(b.split()) for b in text.split('\n') if b.strip()] or [norm(text.split())]
    from difflib import SequenceMatcher
    for name, v in json.load(open(trpath)).items():          # 0) strict word-for-word diff per clip vs its script block
        hyp = norm([x['text'] for x in v['words']])
        best = max(blocks, key=lambda b: SequenceMatcher(None, b, hyp, autojunk=False).ratio())
        fails += diffs(best, hyp, os.path.basename(name))
    for w in sorted(script):                       # 1) every risky script word must be heard spelled exactly
        if risky(w) and w not in heard:
            fails += 1; print(f"FAIL  risky word not heard as spelled: {w}  (Whisper gave: {sorted(h for h in heard if h not in script and zf(h,'en')==0)})")
    for t in sorted(heard - script):               # 2) any non-word Whisper emitted is a mispronunciation signal
        if zf(t, 'en') == 0: fails += 1; print(f"FAIL  non-word in transcript: {t}")
    if fails: print(f"\n{fails} problem(s): fix BEFORE delivery (re-read the verse block alone, trim, or swap the word).")
    else:
        for w in script:
            if risky(w) and w in heard: led[w] = {'status': 'ok', 'src': os.path.basename(trpath)}
        save(led); print("PASS - risky words heard as spelled, no non-words; ledger updated")
    return fails
def compare(a, b):
    A = json.load(open(a)); B = json.load(open(b)); n = 0
    for k in A:
        if k in B: n += diffs(norm([x['text'] for x in A[k]['words']]), norm([x['text'] for x in B[k]['words']]), os.path.basename(k))
    print(f"{n} disagreement(s) between the two models" if n else "models agree word for word"); return n
def seed(paths):
    led = load(); n = 0
    for p in paths:
        for t in set(tokens(json.load(open(p)))):
            if len(t) > 3 and risky(t) and zf(t, 'en') > 0 and t not in led: led[t] = {'status': 'ok', 'src': 'whisper-heard-' + os.path.basename(p)}; n += 1
    save(led); print(f"seeded {n} words, ledger now {len(led)}")
if __name__ == '__main__':
    c = sys.argv[1:2]
    if c == ['scan']: sys.exit(1 if scan(sys.argv[2]) else 0)
    elif c == ['check']: sys.exit(1 if check(sys.argv[2], sys.argv[3]) else 0)
    elif c == ['compare']: sys.exit(1 if compare(sys.argv[2], sys.argv[3]) else 0)
    elif c == ['seed']: seed(sys.argv[2:])
    else: print(__doc__)
