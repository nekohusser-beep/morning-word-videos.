#!/usr/bin/env python3
"""timings.json -> captions.ass (burned-in bottom captions + a big title card). Poppins, soft colors."""
import json, re, sys, textwrap

SP = sys.argv[1]
d = json.load(open(f"{SP}/timings.json"))
THINK_HOLD = 5.5   # seconds the question stays on screen after it is spoken
MAXC = 100       # characters per card (two lines of about 50)
WRAP = 50


def split_cards(text):
    if len(text) <= MAXC:
        return [text]
    mid = len(text) / 2
    cands = [m.end() for m in re.finditer(r"[,;:?!](?=\s)", text)]
    cands = [c for c in cands if 18 <= c <= len(text) - 18]
    if not cands:
        cands = [m.end() for m in re.finditer(r"\s", text) if 18 <= m.end() <= len(text) - 18]
    if not cands:
        return [text]
    c = min(cands, key=lambda x: abs(x - mid))
    return split_cards(text[:c].strip()) + split_cards(text[c:].strip())


def ts(x):
    x = max(0.0, x)
    h = int(x // 3600)
    m = int((x % 3600) // 60)
    s = x - h * 3600 - m * 60
    cs = int(round((s - int(s)) * 100))
    si = int(s)
    if cs == 100:
        cs = 0
        si += 1
    return f"{h}:{m:02d}:{si:02d}.{cs:02d}"


def wrap(text):
    if len(text) <= 38:
        return text
    sp = [m.start() for m in re.finditer(" ", text)]
    c = min(sp, key=lambda x: abs(x - len(text) / 2))
    return text[:c] + "\\N" + text[c + 1:]


hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Narr,Poppins Light,68,&H00F2E8E3&,&H000000FF,&H00180E0A&,&H90000000&,0,0,0,0,100,100,0.5,0,1,3.4,1.8,2,150,150,62,1
Style: Quote,Poppins Light,68,&H00C6E8FF&,&H000000FF,&H00180E0A&,&H90000000&,0,-1,0,0,100,100,0.5,0,1,3.4,1.8,2,150,150,62,1
Style: Think,Poppins Light,68,&H00F2E8E3&,&H000000FF,&H00180E0A&,&H90000000&,0,0,0,0,100,100,0.5,0,1,3.4,1.8,2,150,150,62,1
Style: Title,Poppins,168,&H00F4EDE6&,&H000000FF,&H00241410&,&H80000000&,-1,0,0,0,100,100,2,0,1,4,3,5,120,120,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
out = [hdr]
for u in d["units"]:
    if u["kind"] == "title":
        a, b = 1.0, u["t1"] + 4.2
        out.append(f"Dialogue: 0,{ts(a)},{ts(b)},Title,,0,0,0,,{{\\an5\\pos(960,420)\\fad(1400,1800)}}{wrap(u['text']).replace(chr(92) + 'N', chr(92) + 'N')}\n")
        continue
    if u["kind"] == "think":
        # gold small-caps label above the question; card stays up through the quiet pause, then fades
        a, b = u["t0"] - 0.05, u["t1"] + THINK_HOLD
        lab = "{\\fs46\\b1\\c&H005CCEFF&\\fsp7\\bord3}SOMETHING TO THINK ABOUT{\\r}\\N"
        out.append(f"Dialogue: 0,{ts(a)},{ts(b)},Think,,0,0,0,,{{\\fad(700,1200)}}{lab}{wrap(u['text'])}\n")
        continue
    cards = split_cards(u["text"])
    tot = sum(len(c) for c in cards)
    t0, span = u["t0"], u["t1"] - u["t0"]
    pos = 0
    for i, c in enumerate(cards):
        a = t0 + span * pos / tot
        pos += len(c)
        b = t0 + span * pos / tot
        end = b + (0.55 if i == len(cards) - 1 else 0.0)
        style = "Quote" if u["kind"] == "quote" else "Narr"
        out.append(f"Dialogue: 0,{ts(a - 0.05)},{ts(end)},{style},,0,0,0,,{{\\fad(350,450)}}{wrap(c)}\n")
open(f"{SP}/captions.ass", "w", encoding="utf-8").write("".join(out))
print("cards", len(out) - 1)
