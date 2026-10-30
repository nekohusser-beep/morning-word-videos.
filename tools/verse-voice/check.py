"""Whisper word check of an audition wav against the exact KJV text (numerals/punctuation normalised)."""
import sys, re, json
from faster_whisper import WhisperModel
wav = sys.argv[1]
want = " ".join(json.load(open("tools/verse-voice/text.json"))["segments"])
norm = lambda s: re.sub(r"[^a-z ]", "", s.lower().replace("-", " ")).split()
m = WhisperModel("medium.en", device="cpu", compute_type="int8")
segs, _ = m.transcribe(wav, language="en", beam_size=5)
got = " ".join(s.text for s in segs)
w, g = norm(want), norm(got)
# word-level edit distance
d = [[0] * (len(g) + 1) for _ in range(len(w) + 1)]
for i in range(len(w) + 1): d[i][0] = i
for j in range(len(g) + 1): d[0][j] = j
for i in range(1, len(w) + 1):
    for j in range(1, len(g) + 1):
        d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + (w[i-1] != g[j-1]))
print("HEARD:", got.strip())
print("WORD ERRORS:", d[len(w)][len(g)], "of", len(w), "words")
