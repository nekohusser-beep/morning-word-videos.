#!/usr/bin/env python3
"""Find LIVE Blessed Morning Shorts whose description repeats a cut-off piece of the verse (posts.py bug, fixed
Nov 26 2026) and print one yt-push job per video. Read-only: it changes nothing. Claude writes the printed jobs
into tools/yt-push/queue/ and pushes; yt-push then saves a rollback, applies and re-reads to verify."""
import glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "yt-push"))
import yt_push  # noqa: E402

tok = yt_push.get_token(False)
if not tok:
    sys.exit("no working sign-in")
yt = yt_push.YT(token=tok)
vids = yt_push.channel_videos(yt)
eps = []
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "eps", "m-*.json"))):
    e = json.load(open(f)); kjv = e.get("kjv", "")
    frag = [l["say"] for l in e["lines"] if l["big"] == l["say"] and l["big"].strip() in kjv and l["big"].strip() != kjv.strip()]
    own = [l["say"] for l in e["lines"] if l["big"] == l["say"] and l["big"].strip() not in kjv]
    if frag and kjv:
        eps.append((kjv, frag, own[0] if own else ""))
n = 0
for title, v in vids.items():
    d = (v.get("snippet") or {}).get("description", "")
    for kjv, frag, own in eps:
        if kjv[:40] not in d:
            continue
        for fr in frag:
            bad = "\n\n" + fr + "\n\n"
            if bad in d:
                new = d.replace(bad, ("\n\n" + own + "\n\n") if own else "\n\n", 1)
                print("JOB " + json.dumps({"video_id": v["id"], "description": new, "_title": title, "_privacy": v.get("privacy")}, ensure_ascii=False))
                n += 1
print("videos on channel: %d | live descriptions to fix: %d" % (len(vids), n))
