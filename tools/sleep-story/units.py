#!/usr/bin/env python3
"""script_v2.txt -> units.json. Script format: 'T: ' title, plain lines narration, '» ' KJV quote, '? ' think-about question, blank = paragraph break.
Each unit: idx, kind (title|narr|quote|think), text (caption text), para_end, in_line."""
import json, re, sys
SP = sys.argv[1]
src = sys.argv[2] if len(sys.argv) > 2 else "script_v2.txt"
lines = [l.rstrip("\n") for l in open(f"{SP}/{src}", encoding="utf-8")]
units = []
for l in lines:
    if not l.strip():
        if units: units[-1]["para_end"] = True
        continue
    if l.startswith("T: "):
        units.append(dict(kind="title", text=l[3:].strip(), para_end=False, in_line=False))
    elif l.startswith("» "):
        units.append(dict(kind="quote", text=l[2:].strip(), para_end=False, in_line=False))
    elif l.startswith("? "):
        units.append(dict(kind="think", text=l[2:].strip(), para_end=False, in_line=False))
    else:
        sents = re.split(r"(?<=[.!?])\s+(?=[A-Z])", l.strip())
        for j, s in enumerate(sents):
            units.append(dict(kind="narr", text=s, para_end=False, in_line=(j < len(sents) - 1)))
for i, u in enumerate(units): u["idx"] = i
json.dump(units, open(f"{SP}/units.json", "w"), indent=1)
from collections import Counter
print("units", len(units), dict(Counter(u["kind"] for u in units)))
