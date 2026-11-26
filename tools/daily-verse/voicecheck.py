#!/usr/bin/env python3
"""Voice check for the daily verse cards. Run BEFORE building or queueing any new card batch.

Why (Nov 26 2026): the card voice sounds words out from their spelling and got five Bible words wrong
("goest" came out as "ghost", "hast" as "haste", "strengtheneth", "Zephaniah", "commune") plus five everyday
words with two pronunciations ("wind down", "tear them down", "live like it", "use the time", "read slowly").
Whisper did not catch them because its language model writes the word it expects. This check does not listen:
it shows how the voice WILL sound out every word nobody has reviewed yet, so the review happens before a build.

  KOKORO_DIR=<dir with the model> python3 tools/daily-verse/voicecheck.py            # check every card script
  ... voicecheck.py --accept      # after reviewing the printed sounds: add them to voice_vetted.json

PASS (exit 0) = every spoken word is either reviewed (voice_vetted.json) or has a fix in build.py FIX.
FAIL (exit 1) = new words or new uses of a two-way word: read the sounds printed, then either --accept or add
a fix to FIX in build.py (sounds, never a respelling: Scripture text is not touched).
After any FIX change, prove it with phonemes.yml on the spoken line (see kingdom-brain workflows/card-voice.md)."""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "voice_vetted.json")
TWO_WAY = ["live", "lives", "tear", "wind", "close", "use", "read", "lead", "present", "perfect", "wound", "bow",
           "desert", "content", "object", "record", "minute", "refuse", "house", "does", "learned", "blessed", "aged", "sow", "bass", "dove"]

src = open(os.path.join(HERE, "build.py")).read()
ns = {}
exec(src[src.index("FIX = {"):src.index("_FIXRX")], ns)
FIX = ns["FIX"]
led = json.load(open(LEDGER)) if os.path.exists(LEDGER) else {"words": [], "contexts": []}
vetted, ctx_ok = set(led["words"]), set(led["contexts"])

from kokoro_onnx import Kokoro  # noqa: E402
KD = os.environ.get("KOKORO_DIR", ".")
k = Kokoro(f"{KD}/kokoro-v1.0.onnx", f"{KD}/voices-v1.0.bin")
ph = lambda t: k.tokenizer.phonemize(t, "en-us")  # noqa: E731

new_words, new_ctx = {}, {}
for f in sorted(glob.glob(os.path.join(HERE, "eps", "[mn]-*.json"))):
    e = json.load(open(f)); card = os.path.basename(f)[:-5]
    for l in e["lines"]:
        say = l["say"]
        for w in re.findall(r"[A-Za-z']+", say):
            lw = w.lower().strip("'")
            if lw and lw not in vetted and lw not in FIX:
                new_words.setdefault(lw, card)
        for w in TWO_WAY:
            for m in re.finditer(r"((?:\S+\s+){0,2})\b(%s)\b((?:\s+\S+){0,2})" % w, say, re.I):
                win = re.sub(r"\s+", " ", (m.group(1) + m.group(2) + m.group(3))).strip().lower()
                if win in ctx_ok or any(p in win for p in FIX if " " in p):
                    continue
                new_ctx.setdefault(win, card)

if "--accept" in sys.argv:
    led = {"words": sorted(vetted | set(new_words)), "contexts": sorted(ctx_ok | set(new_ctx))}
    json.dump(led, open(LEDGER, "w"), indent=0, ensure_ascii=False)
    print("accepted %d words and %d uses into voice_vetted.json" % (len(new_words), len(new_ctx)))
    sys.exit(0)
for w, card in sorted(new_words.items()):
    print("NEW WORD  %-16s sounds like %-22s (%s)" % (w, ph(w), card))
for win, card in sorted(new_ctx.items()):
    print("TWO-WAY   %-40s sounds like %s (%s)" % ('"%s"' % win, ph(win), card))
print("VOICE CHECK: %s (%d new words, %d new two-way uses; %d fixes in build.py)" % (
    "PASS" if not (new_words or new_ctx) else "FAIL: review the sounds above", len(new_words), len(new_ctx), len(FIX)))
sys.exit(1 if (new_words or new_ctx) else 0)
