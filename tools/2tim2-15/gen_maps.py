"""Writes tr/large-v3.json (keys tx/cNN.wav, NN = line number) and clipmap.json for the 2 Timothy 2:15 build.
Whisper large-v3 word times come from the draft-release transcripts (2tim2-15-nov05); the first word of every clip is snapped
to 0.00 by Whisper, so it is reset to the measured speech onset. Line 2 is stretched (picture and voice together)."""
import json, os, sys
W = os.path.dirname(os.path.abspath(__file__))
S = os.environ["SCR"]
SRC = {1:"c12",2:"c13",3:"c11",4:"c14",5:"c04",6:"r00",7:"c10",8:"c18",9:"c05",10:"c06",11:"c09",12:"c08",13:"c03",14:"c02",15:"c07"}
STRETCH = {2: 1.30}      # slowed in the edit (picture and voice together, never a speed-up)
VCSTRETCH = {9: 1.10}    # Seed-VC run with --length-adjust 1.1 so the unstressed 'a' in 'for a living' survives (picture is B-roll, so no lip-sync to keep)
# measured speech bounds on the source clip: (on, off). 10 ms RMS, onset pk-16 dB, end = min(last frame above pk-24 dB, last word end + 0.25)
B = {1:(0.66,6.69),2:(0.11,3.83),3:(0.55,6.41),4:(0.57,6.67),5:(0.89,6.40),6:(0.88,4.04),7:(1.00,3.62),8:(0.55,4.27),
     9:(0.64,6.09),10:(0.17,6.67),11:(0.65,6.13),12:(0.36,6.57),13:(0.35,6.36),14:(0.39,4.81),15:(0.69,4.15)}
GAP = {k: 0.45 for k in range(1, 16)}; GAP.update({4:0.75, 7:0.75, 8:0.60, 14:0.60, 15:0.0})
T = {}
for f in ["tr2/transcript-42018174662.json","tr3/transcript-42019270969.json","tr4/transcript-42020452697.json","tr5/transcript-42021112385.json"]:
    for k, v in json.load(open(f"{S}/{f}")).items(): T[os.path.basename(k)[:-4]] = v
out = {}; cm = {}
for ln, c in SRC.items():
    F = STRETCH.get(ln, 1.0) * VCSTRETCH.get(ln, 1.0)
    words = []
    for i, w in enumerate(T[c]["words"]):
        st, en = w["start"] * F, w["end"] * F
        if i == 0: st = max(st, B[ln][0] * F)
        words.append({"text": w["text"], "start": round(st, 3), "end": round(en, 3)})
    nm = f"c{ln:02d}"
    out[f"tx/{nm}.wav"] = {"words": words, "text": T[c]["text"]}
    on, off = B[ln]
    cm[str(ln)] = [nm, round(on * F, 3), round(off * F, 3), 0, GAP[ln]]
os.makedirs(f"{W}/tr", exist_ok=True)
json.dump(out, open(f"{W}/tr/large-v3.json", "w"), indent=1)
json.dump(cm, open(f"{W}/clipmap.json", "w"), indent=1)
print("wrote tr/large-v3.json and clipmap.json")
