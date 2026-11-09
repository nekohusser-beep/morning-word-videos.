#!/usr/bin/env python3
"""No-key YouTube keyword research (IQ Vid fallback).
Uses yt-dlp search (no API key) + YouTube autocomplete. Output: top results with
views, views/day, channel, length, tags; outliers vs median; common title words;
autocomplete phrases. Usage: research.py "query" [count]"""
import json, subprocess, sys, statistics, urllib.request, urllib.parse, re
from collections import Counter
from datetime import datetime, timezone

q = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
# flat search reads the results page only (datacenter IPs get bot-checked on full video pages)
res = subprocess.run(["yt-dlp", f"ytsearch{n}:{q}", "--flat-playlist", "--dump-json",
                      "--ignore-errors"], capture_output=True, text=True)
out = res.stdout
if not out.strip():
    print("yt-dlp stderr:", res.stderr[-800:])
rows = []
now = datetime.now(timezone.utc)
for line in out.splitlines():
    try: v = json.loads(line)
    except Exception: continue
    ud = v.get("upload_date") or (datetime.fromtimestamp(v["timestamp"], timezone.utc).strftime("%Y%m%d") if v.get("timestamp") else None)
    age = max(1, (now - datetime.strptime(ud, "%Y%m%d").replace(tzinfo=timezone.utc)).days) if ud else None
    views = v.get("view_count") or 0
    rows.append(dict(id=v.get("id"), title=v.get("title", ""), ch=v.get("channel") or v.get("uploader") or "",
                     subs=v.get("channel_follower_count"), views=views, age=age,
                     vpd=round(views / age) if age else None, dur=v.get("duration"),
                     tags=v.get("tags") or []))
print(f"QUERY: {q}  results: {len(rows)}")
if not rows:
    sys.exit(0)
med = statistics.median([r["views"] for r in rows]) or 1
print(f"median views: {int(med)}")
print("\nTOP RESULTS (views | views/day | x median | length | channel subs | title)")
for r in rows:
    flag = " OUTLIER" if r["views"] >= 3 * med else ""
    print(f"{r['views']:>10} | {r['vpd'] or '-':>7} | {r['views']/med:4.1f}x | {r['dur'] or '-':>5}s | "
          f"{r['subs'] or '-'} | {r['title']} [{r['ch']}] https://youtu.be/{r['id']}{flag}")
words = Counter(w for r in rows for w in re.findall(r"[a-z0-9']+", r["title"].lower()) if len(w) > 2)
print("\nTITLE WORDS:", ", ".join(f"{w}({c})" for w, c in words.most_common(25)))
tags = Counter(t.lower() for r in rows for t in r["tags"])
print("TOP TAGS:", ", ".join(f"{t}({c})" for t, c in tags.most_common(30)))
try:
    u = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(
        {"client": "firefox", "ds": "yt", "q": q})
    sug = json.loads(urllib.request.urlopen(u, timeout=15).read().decode("utf-8", "ignore"))[1]
    print("AUTOCOMPLETE:", " | ".join(sug))
except Exception as e:
    print("AUTOCOMPLETE: failed", e)
