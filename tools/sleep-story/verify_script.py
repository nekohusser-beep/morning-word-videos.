import json, re, sys
SP = sys.argv[1]
def norm(s):
    return re.sub(r"\s+", " ", s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')).strip()
books = {}
for b in ("Exodus", "Hebrews", "1John"):
    d = json.load(open(f"{SP}/pilot/{b}.json"))
    books[b] = [norm(v["text"]) for c in d["chapters"] for v in c["verses"]]
alltext = [t for b in books.values() for t in b]
bad = 0; n = 0
for ln, line in enumerate(open(f"{SP}/script.txt", encoding="utf-8"), 1):
    if line.startswith("» "):
        q = norm(line[2:])
        n += 1
        hit = [t for t in alltext if q in t]
        if not hit:
            # try dropping trailing punctuation
            q2 = q.rstrip(",:;. ")
            hit = [t for t in alltext if q2 in t]
            if not hit:
                bad += 1
                print("NO MATCH line", ln, ":", q)
print("quotes checked", n, "unmatched", bad)
