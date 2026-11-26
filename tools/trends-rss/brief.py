"""Daily TREND BRIEF for the verse cards and any new video (Neko, Nov 25 2026):
'get the trends, find the ones in our niche, read everyone else's description of what's trending,
take the top three and write our own script from that'.
Reads today's reports/trends-rss/<date>.json (current events), searches YouTube for our niche phrases
(uploads this week), takes the fastest movers (views per day), opens the top 3 per phrase and
the top 3 overall to read their descriptions, and pulls the Bible references they use.
Writes reports/trend-brief/<date>.md (+ .json). Claude writes OUR script from it; never copy theirs.
"""
import json, os, re, sys, time, datetime, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "iqvid"))
import iqvid  # serp(), get()

SEEDS = os.environ.get("SEEDS", "morning prayer|night prayer before sleep|bible verse of the day|"
                       "prayer for anxiety|good morning bible verse|psalm 91 prayer").split("|")
WEEK = "EgQIAxAB"   # uploaded this week, videos only
BOOKS = ("Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|Samuel|Kings|Chronicles|Ezra|"
         "Nehemiah|Esther|Job|Psalms?|Proverbs|Ecclesiastes|Song of Solomon|Isaiah|Jeremiah|Lamentations|"
         "Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|"
         "Malachi|Matthew|Mark|Luke|John|Acts|Romans|Corinthians|Galatians|Ephesians|Philippians|Colossians|"
         "Thessalonians|Timothy|Titus|Philemon|Hebrews|James|Peter|Jude|Revelation")
REF = re.compile(r"\b((?:[123] )?(?:%s)) (\d{1,3}):(\d{1,3})" % BOOKS, re.I)
ET = datetime.timezone(datetime.timedelta(hours=-5))

_TOK = {}

def _signin_token():
    """Access token from the saved yt-push sign-in (needs YT_CLIENT_ID + YT_CLIENT_SECRET in the env). '' if none."""
    if "t" not in _TOK:
        _TOK["t"] = ""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "yt-push"))
            import yt_push  # noqa
            _TOK["t"] = yt_push.get_token(False) or ""
        except Exception as e:  # noqa
            print("sign-in token not available: %s" % str(e)[:100])
    return _TOK["t"]

def description(vid):
    # Official route first (Neko Nov 26 2026, GROW head-to-head): the YouTube Data API returns the FULL description.
    # The watch-page scrape below came back blank from runners every time. Key goes in a header, never the URL,
    # so a failed call can never print it. Costs 1 of the 10,000 free daily quota units per video.
    # Auth: the API key if this repo has one, otherwise the channel sign-in yt-push already uses (read-only call).
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    auth = {"X-Goog-Api-Key": key} if key else None
    if not auth:
        tok = _signin_token()
        auth = {"Authorization": "Bearer " + tok} if tok else None
    if auth:
        try:
            j = json.loads(iqvid.get("https://www.googleapis.com/youtube/v3/videos?part=snippet&id=%s" % vid,
                                     tries=2, headers=auth))
            items = j.get("items") or []
            if items and items[0].get("snippet", {}).get("description"):
                return items[0]["snippet"]["description"]
        except Exception as e:  # noqa
            secret = key or (auth.get("Authorization", "")[7:])
            print("api description failed for %s: %s" % (vid, str(e).replace(secret, "[secret]")[:120] if secret else str(e)[:120]))
    try:
        html = iqvid.get("https://www.youtube.com/watch?v=%s&hl=en&gl=US" % vid)
        m = re.search(r'"shortDescription":"((?:[^"\\]|\\.)*)"', html)
        return json.loads('"%s"' % m.group(1)) if m else ""
    except Exception as e:  # noqa
        return ""

def opening(vid, n=14):
    """The first words a mover actually SPEAKS plus how long its script is, read through Firecrawl keyless (no account,
    no key, free; capped per IP per day, so a miss just leaves the line out). Added Nov 26 2026 (GROW head-to-head):
    Firecrawl returns the full transcript of a watch page. Kept to a few words on purpose: study the hook, never copy."""
    try:
        body = json.dumps({"url": "https://www.youtube.com/watch?v=%s" % vid, "formats": ["markdown"]}).encode()
        raw = iqvid.get("https://api.firecrawl.dev/v2/scrape", tries=1, timeout=90, data=body,
                        headers={"Content-Type": "application/json"})
        md = (json.loads(raw).get("data") or {}).get("markdown") or ""
        m = re.search(r"## Transcript\s+(.+)", md, re.S)
        words = re.sub(r"\s+", " ", m.group(1)).strip().split() if m else []
        if len(words) < 20:
            return ""
        return '"%s..." (%d words spoken)' % (" ".join(words[:n]), len(words))
    except Exception as e:  # noqa
        print("opening not read for %s: %s" % (vid, str(e)[:100]))
        return ""

def clean(d, n=700):
    d = re.sub(r"https?://\S+", "", d)
    d = re.sub(r"#\w+", "", d)
    return re.sub(r"\s+", " ", d).strip()[:n]

def main():
    day = datetime.datetime.now(ET).strftime("%Y-%m-%d")
    events = []
    p = "reports/trends-rss/%s.json" % day
    if os.path.exists(p):
        events = json.load(open(p))["items"]
    per, allrows = {}, {}
    for s in SEEDS:
        rows, _ = iqvid.serp(s, pages=1, sp=WEEK)
        rows = [r for r in rows if r.get("views") and not r.get("live")]
        for r in rows:
            r["vpd"] = r["views"] / max(r.get("age") or 1, 0.5)
            r["seed"] = s
        rows.sort(key=lambda r: -r["vpd"])
        per[s] = rows[:3]
        for r in rows[:6]:
            allrows.setdefault(r["id"], r)
        time.sleep(1)
    top = sorted(allrows.values(), key=lambda r: -r["vpd"])[:3]
    need = {r["id"] for v in per.values() for r in v} | {r["id"] for r in top}
    desc = {}
    for vid in need:
        desc[vid] = description(vid)
        time.sleep(0.7)
    refs = collections.Counter()
    for vid in need:
        r = allrows.get(vid) or next(x for v in per.values() for x in v if x["id"] == vid)
        for b, c, v in REF.findall(r["title"] + " " + desc[vid]):
            refs["%s %s:%s" % (b.title(), c, v)] += 1
    L = ["# Trend brief %s" % day, "",
         "Use: pick tonight's/tomorrow's card verse and angle from this; read the top 3, then write OUR own script",
         "(KJV only, never reword scripture, first word on frame 1, open on the viewer's tension). Never copy their text.", ""]
    L += ["## Current events (Google Trends US)", ""]
    hooks = [e for e in events if e.get("hook")]
    for e in (hooks or events)[:6]:
        L.append("- %s%s (%s) - %s" % ("HOOK: " if e.get("hook") else "", e["query"], e["traffic"],
                                       e["news"][0]["title"] if e.get("news") else ""))
    if not hooks:
        L.append("- (no faith-adjacent trend today: keep the card on the niche winners below)")
    L += ["", "## Top 3 in our niche this week (fastest views/day)", ""]
    for i, r in enumerate(top, 1):
        L.append("%d. **%s** - %s - %s views, %.0f/day, %s - youtu.be/%s" % (
            i, r["title"], r["ch"], format(r["views"], ","), r["vpd"], "Short" if (r.get("dur") or 999) <= 180 else "long", r["id"]))
        L.append("   - what they say: %s" % (clean(desc[r["id"]]) or "(runner could not read it: open the link in the browser before writing)"))
        o = opening(r["id"])
        if o:
            L.append("   - their first words: %s" % o)
    L += ["", "## Verses the movers are using", ""]
    L.append(", ".join("%s (x%d)" % kv for kv in refs.most_common(10)) or "(none found)")
    L += ["", "## Top 3 per phrase", ""]
    for s, rows in per.items():
        L.append("### %s" % s)
        for r in rows:
            L.append("- %s - %s - %s views, %.0f/day - youtu.be/%s | %s" % (
                r["title"], r["ch"], format(r["views"], ","), r["vpd"], r["id"], clean(desc[r["id"]], 220)))
        L.append("")
    os.makedirs("reports/trend-brief", exist_ok=True)
    open("reports/trend-brief/%s.md" % day, "w").write("\n".join(L) + "\n")
    json.dump({"events": events[:10], "top": top, "per": per, "refs": refs.most_common(20),
               "desc": {k: clean(v, 1500) for k, v in desc.items()}},
              open("reports/trend-brief/%s.json" % day, "w"), indent=1, default=str)
    print("\n".join(L[:60]))

if __name__ == "__main__":
    main()
