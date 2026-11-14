#!/usr/bin/env python3
"""IQ Vid v2 engine (our own vidIQ). No API key, standard library only.
Built to run on a GitHub runner (the Claude sandbox cannot reach YouTube).

Modes (queries separated by |):
  kw    "seed|seed2"   keyword table: autocomplete tree (related / matching / questions),
                       real search-page stats per keyword, competition 0-100, views/day demand
  out   "topic|topic2" long-video outliers, scored against each channel's own median views
                       (the way vidIQ and Studio score them), plus title patterns of the winners
  batch "k1|k2|..."    search-page features only (used to calibrate the competition score)

Writes <out>.json (everything) and <out>.txt (short readout).
Search volume itself comes from Google Trends in the browser pane (kingdom-brain tools/iqvid/trends.js);
this script also tries Trends from the runner and records whether it worked.
"""
import sys, re, json, time, math, statistics, argparse, os
import urllib.request, urllib.parse, http.cookiejar
from collections import Counter, OrderedDict

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/131.0.0.0 Safari/537.36")
HDR = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
       "Cookie": "SOCS=CAI; CONSENT=YES+1; PREF=hl=en&gl=US"}
STOP = set("a an the of to in on for and or is are was were be with at by from as it this that your you my "
           "his her their our vs".split())
QWORDS = ["how", "why", "what", "who", "when", "where", "is", "did", "can", "does"]
LONG_MIN = 181          # Shorts run up to 3 minutes, so a long video is 3:01 or more


def get(url, tries=3, timeout=25, data=None, headers=None):
    last = None
    for i in range(tries):
        try:
            h = dict(HDR)
            if headers:
                h.update(headers)
            req = urllib.request.Request(url, headers=h, data=data)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:  # noqa
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError("GET failed %s: %s" % (url[:90], last))


def num(s):
    if not s:
        return None
    s = s.replace(" ", " ")
    m = re.search(r"(\d[\d.,]*)\s*([KMB])?\b", s, re.I)
    if not m:
        return 0 if re.search(r"\bno\b", s, re.I) else None
    try:
        v = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    return int(v * {"K": 1e3, "M": 1e6, "B": 1e9}.get((m.group(2) or "").upper(), 1))


UNITS = {"second": 1 / 86400, "minute": 1 / 1440, "hour": 1 / 24, "day": 1, "week": 7, "month": 30.44,
         "year": 365.25}


def age_days(s):
    """'8 months ago' -> days. YouTube rounds down, so add half a unit for day and bigger."""
    m = re.search(r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", s or "")
    if not m:
        return None
    n, u = int(m.group(1)), m.group(2)
    if u in ("day", "week", "month", "year"):
        n += 0.5
    return round(n * UNITS[u], 2)


def dur_s(s):
    s = (s or "").strip()
    if not re.match(r"^\d+(:\d\d){1,2}$", s):
        return None
    t = 0
    for x in s.split(":"):
        t = t * 60 + int(x)
    return t


def initial_data(html):
    m = re.search(r'(?:var\s+ytInitialData|window\["ytInitialData"\])\s*=\s*', html)
    if not m:
        return None
    try:
        return json.JSONDecoder().raw_decode(html, m.end())[0]
    except Exception:  # noqa
        return None


def walk(o, keys, out=None):
    if out is None:
        out = []
    if isinstance(o, dict):
        for k, v in o.items():
            if k in keys and isinstance(v, dict):
                out.append((k, v))
            else:
                walk(v, keys, out)
    elif isinstance(o, list):
        for v in o:
            walk(v, keys, out)
    return out


def txt(o):
    if not o:
        return ""
    if isinstance(o, str):
        return o
    if "simpleText" in o:
        return o["simpleText"]
    if isinstance(o.get("content"), str):
        return o["content"]
    return "".join(r.get("text", "") for r in o.get("runs", []) or [])


def parse_vr(v):
    owner = (v.get("ownerText") or v.get("longBylineText") or v.get("shortBylineText") or {}).get("runs") or [{}]
    o0 = owner[0]
    be = (o0.get("navigationEndpoint") or {}).get("browseEndpoint") or {}
    vt = txt(v.get("viewCountText"))
    live = "watching" in vt
    return dict(id=v.get("videoId"), title=txt(v.get("title")), views=(None if live else num(vt)),
                age=age_days(txt(v.get("publishedTimeText"))), dur=dur_s(txt(v.get("lengthText"))),
                ch=o0.get("text", ""), chid=be.get("browseId", ""), live=live,
                short=("reelWatchEndpoint" in (v.get("navigationEndpoint") or {})))


def parse_lockup(l):
    if l.get("contentType") not in (None, "LOCKUP_CONTENT_TYPE_VIDEO"):
        return None
    md = (l.get("metadata") or {}).get("lockupMetadataViewModel") or {}
    parts = []
    rows = ((md.get("metadata") or {}).get("contentMetadataViewModel") or {}).get("metadataRows") or []
    for row in rows:
        for p in row.get("metadataParts") or []:
            parts.append(txt(p.get("text")))
    views = next((num(p) for p in parts if re.search(r"\bviews?\b", p)), None)
    age = next((age_days(p) for p in parts if " ago" in p), None)
    ch = next((p for p in parts if p and "view" not in p and " ago" not in p), "")
    blob = json.dumps(l)
    d = re.search(r'"text":\s*"(\d+(?::\d\d){1,2})"', blob)
    cid = re.search(r'"browseId":\s*"(UC[\w-]{22})"', blob)
    return dict(id=l.get("contentId"), title=txt(md.get("title")), views=views, age=age,
                dur=dur_s(d.group(1)) if d else None, ch=ch, chid=cid.group(1) if cid else "",
                live=False, short=False)


def rows_from(data):
    rows, seen = [], set()
    for k, v in walk(data, {"videoRenderer", "lockupViewModel", "gridVideoRenderer"}):
        r = parse_lockup(v) if k == "lockupViewModel" else parse_vr(v)
        if r and r.get("id") and r.get("title") and r["id"] not in seen:
            seen.add(r["id"])
            rows.append(r)
    return rows


def serp(q, pages=1, sp="EgIQAQ%3D%3D"):
    """Real YouTube search results for q (videos only). Returns (rows, estimated result count)."""
    url = ("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(q) + "&hl=en&gl=US"
           + ("&sp=" + sp if sp else ""))
    html = get(url)
    data = initial_data(html)
    if not data:
        return [], None
    rows = rows_from(data)
    est = data.get("estimatedResults")
    est = int(est) if est and str(est).isdigit() else None
    ver = re.search(r'"INNERTUBE_CLIENT_VERSION":"([\d.]+)"', html)
    blob = json.dumps(data)
    for _ in range(max(0, pages - 1)):
        tok = re.findall(r'"continuationCommand":\s*\{"token":\s*"([^"]+)"', blob)
        if not tok or not ver:
            break
        body = json.dumps({"context": {"client": {"clientName": "WEB", "clientVersion": ver.group(1),
                                                    "hl": "en", "gl": "US"}},
                           "continuation": tok[-1]}).encode()
        try:
            more = json.loads(get("https://www.youtube.com/youtubei/v1/search?prettyPrint=false", data=body,
                                  headers={"Content-Type": "application/json"}))
        except Exception:  # noqa
            break
        have = {r["id"] for r in rows}
        rows += [r for r in rows_from(more) if r["id"] not in have]
        blob = json.dumps(more)
        time.sleep(0.3)
    return rows, est


_CH = {}


def channel(chid):
    """Subscribers and the median views of the channel's recent long videos (the outlier baseline)."""
    if chid in _CH:
        return _CH[chid]
    info = dict(subs=None, med=None, n=0)
    try:
        html = get("https://www.youtube.com/channel/%s/videos?hl=en&gl=US" % chid)
        m = re.search(r'"([\d.,]+\s?[KMB]?) subscribers?"', html)
        if m:
            info["subs"] = num(m.group(1))
        vs = [r for r in rows_from(initial_data(html) or {}) if r.get("views") is not None][:30]
        base = [r["views"] for r in vs if (r.get("age") or 99) >= 7] or [r["views"] for r in vs]
        if len(base) >= 5:
            info["med"] = int(statistics.median(base))
            info["n"] = len(base)
    except Exception as e:  # noqa
        info["err"] = str(e)[:80]
    _CH[chid] = info
    time.sleep(0.25)
    return info


def suggest(q):
    try:
        u = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(
            {"client": "firefox", "ds": "yt", "hl": "en", "gl": "us", "q": q})
        return json.loads(get(u, tries=2, timeout=12))[1]
    except Exception:  # noqa
        return []


def expand(seed, deep=True):
    """Autocomplete tree: what people really type around the seed."""
    seen = OrderedDict()

    def add(lst, src):
        for i, s in enumerate(lst):
            s = s.strip().lower()
            if s and s != seed.lower() and s not in seen:
                seen[s] = dict(src=src, pos=i)

    add(suggest(seed), "seed")
    add(suggest(seed + " "), "seed")
    if deep:
        for w in QWORDS:
            add(suggest("%s %s" % (w, seed)), "q")
        for c in "abcdefghijklmnopqrstuvwxyz":
            add(suggest("%s %s" % (seed, c)), "az")
    return seen


def tokens(s):
    return [w for w in re.findall(r"[a-z0-9']+", s.lower()) if w not in STOP]


def features(q, rows, est):
    vids = [r for r in rows if not r["live"] and r["views"] is not None][:20]
    t10 = vids[:10]
    if len(t10) < 3:
        return None
    qt = tokens(q)

    def has_all(t):
        tt = t.lower()
        return all(w in tt for w in qt)

    views = [r["views"] for r in t10]
    vpd = [r["views"] / max(r["age"], 1) for r in t10 if r["age"]]
    share = lambda fn: round(sum(1 for r in t10 if fn(r)) / len(t10), 2)  # noqa
    return dict(n=len(vids), est=est, med_views=int(statistics.median(views)), max_views=max(views),
                med_vpd=round(statistics.median(vpd), 1) if vpd else None,
                sum_vpd=int(sum(vpd)) if vpd else None,
                exact=share(lambda r: has_all(r["title"])),
                old=share(lambda r: (r["age"] or 0) > 730),
                fresh=share(lambda r: (r["age"] or 9999) < 180),
                lowbar=share(lambda r: r["views"] < 10000),
                longshare=share(lambda r: (r["dur"] or 0) >= LONG_MIN))


# Competition 0-100. Weights fitted Nov 14 2026 against 35 vidIQ competition scores (see
# kingdom-brain tools/iqvid/CALIBRATION.md). Refit when more vidIQ numbers are logged.
W = dict(b=-12.0, views=9.0, vpd=5.0, exact=6.0, lowbar=-14.0, old=0.0, est=1.5)


def competition(f):
    if not f:
        return None
    x = (W["b"] + W["views"] * math.log10(f["med_views"] + 1) + W["vpd"] * math.log10((f["med_vpd"] or 0) + 1)
         + W["exact"] * f["exact"] + W["lowbar"] * f["lowbar"] + W["old"] * f["old"]
         + W["est"] * math.log10((f["est"] or 0) + 1))
    return int(max(1, min(99, round(x))))


def trends_try(kws):
    """Best effort Google Trends (YouTube search) from the runner. Usually rate limited on
    datacenter IPs; the browser pane helper is the dependable route."""
    try:
        cj = http.cookiejar.CookieJar()
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        op.addheaders = [("User-Agent", UA), ("Accept-Language", "en-US,en;q=0.9")]
        op.open("https://trends.google.com/trends/explore?geo=US&hl=en-US", timeout=20).read()
        req = {"comparisonItem": [{"keyword": k, "geo": "", "time": "today 3-m"} for k in kws[:5]],
               "category": 0, "property": "youtube"}
        u = "https://trends.google.com/trends/api/explore?" + urllib.parse.urlencode(
            {"hl": "en-US", "tz": "300", "req": json.dumps(req, separators=(",", ":"))})
        t = op.open(u, timeout=20).read().decode()
        w = [w for w in json.loads(t[t.index("{"):])["widgets"] if w["id"] == "TIMESERIES"][0]
        u2 = "https://trends.google.com/trends/api/widgetdata/multiline?" + urllib.parse.urlencode(
            {"hl": "en-US", "tz": "300", "req": json.dumps(w["request"], separators=(",", ":")),
             "token": w["token"]})
        t2 = op.open(u2, timeout=20).read().decode()
        td = json.loads(t2[t2.index("{"):])["default"]["timelineData"]
        return {"ok": True, "avg": {k: round(sum(p["value"][i] for p in td) / len(td), 2)
                                    for i, k in enumerate(kws[:5])}}
    except Exception as e:  # noqa
        return {"ok": False, "why": str(e)[:120]}


def fmt(n):
    if n is None:
        return "-"
    for d, s in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= d:
            return ("%.1f" % (n / d)).rstrip("0").rstrip(".") + s
    return str(int(n))


def mode_batch(queries, a):
    res, lines = [], []
    for q in queries:
        try:
            rows, est = serp(q)
            f = features(q, rows, est)
        except Exception as e:  # noqa
            rows, f = [], None
            lines.append("%s: ERROR %s" % (q, e))
        res.append(dict(q=q, f=f, comp=competition(f), rows=rows[:20]))
        if f:
            lines.append("%-34s comp %2s | top10 median %7s | %7s views/day | exact %.1f | weak %.1f | results %s"
                         % (q[:34], competition(f), fmt(f["med_views"]), fmt(f["med_vpd"]), f["exact"],
                            f["lowbar"], fmt(f["est"])))
        time.sleep(0.4)
    return dict(mode="batch", items=res), lines


def mode_kw(queries, a):
    out, lines = [], []
    for seed in queries:
        tree = expand(seed, deep=not a.fast)
        st = set(tokens(seed))
        matching = [k for k in tree if st and st.issubset(set(tokens(k)))]
        questions = [k for k in tree if k.split(" ")[0] in QWORDS]
        related = [k for k in tree if k not in matching and k not in questions]
        pick = [seed] + [k for k in tree if tree[k]["src"] == "seed"][:a.n] + questions[:3]
        pick = list(OrderedDict.fromkeys(pick))
        table = []
        for k in pick:
            try:
                rows, est = serp(k)
                f = features(k, rows, est)
            except Exception:  # noqa
                f = None
            table.append(dict(kw=k, comp=competition(f), f=f))
            time.sleep(0.4)
        tr = trends_try([seed] + pick[1:5])
        out.append(dict(seed=seed, table=table, matching=matching, questions=questions, related=related,
                        trends_runner=tr))
        lines.append("=== KEYWORDS: %s ===" % seed)
        lines.append("keyword | competition | top-10 median views | views/day landing on top 10 | titles using it | weak spots")
        for t in table:
            f = t["f"]
            if f:
                lines.append("%-38s | %2s | %7s | %7s | %3d%% | %3d%%" % (
                    t["kw"][:38], t["comp"], fmt(f["med_views"]), fmt(f["sum_vpd"]), f["exact"] * 100,
                    f["lowbar"] * 100))
            else:
                lines.append("%-38s | no data" % t["kw"][:38])
        lines.append("MATCHING (%d): %s" % (len(matching), " | ".join(matching[:40])))
        lines.append("QUESTIONS (%d): %s" % (len(questions), " | ".join(questions[:25])))
        lines.append("RELATED (%d): %s" % (len(related), " | ".join(related[:40])))
        lines.append("TRENDS FROM RUNNER: %s" % json.dumps(tr))
    return dict(mode="kw", items=out), lines


def mode_out(queries, a):
    out, lines = [], []
    for topic in queries:
        qs = [topic] + [k for k in expand(topic, deep=False)][:a.extra]
        pool = OrderedDict()
        for q in qs:
            try:
                rows, _ = serp(q, pages=a.pages)
            except Exception:  # noqa
                rows = []
            for r in rows:
                if (r["dur"] or 0) >= a.minlen and r["views"] and not r["live"]:
                    pool.setdefault(r["id"], r)
            time.sleep(0.4)
        cand = list(pool.values())
        chans = []
        for r in cand:
            if r["chid"] and r["chid"] not in chans:
                chans.append(r["chid"])
        for cid in chans[:a.channels]:
            channel(cid)
        for r in cand:
            c = _CH.get(r["chid"]) or {}
            r["subs"], r["med"] = c.get("subs"), c.get("med")
            r["x"] = round(r["views"] / c["med"], 1) if c.get("med") else None
            r["vps"] = round(r["views"] / c["subs"], 1) if c.get("subs") else None
            r["vpd"] = int(r["views"] / max(r["age"], 1)) if r["age"] else None
        scored = sorted([r for r in cand if r["x"] is not None], key=lambda r: -r["x"])
        wins = [r for r in scored if r["x"] >= 3]
        words = Counter(w for r in wins for w in set(tokens(r["title"])) if len(w) > 2)
        out.append(dict(topic=topic, queries=qs, pool=len(cand), scored=scored, unscored=[r for r in cand if r["x"] is None]))
        lines.append("=== LONG-VIDEO OUTLIERS: %s (searched: %s) ===" % (topic, "; ".join(qs)))
        lines.append("pool %d long videos, %d scored against their channel's median, %d at 3x or more" % (
            len(cand), len(scored), len(wins)))
        lines.append("outlier | views | views/day | age d | min | subs | channel median | title [channel] link")
        for r in scored[:a.top]:
            lines.append("%5.1fx | %7s | %6s | %5s | %3d | %6s | %6s | %s [%s] https://youtu.be/%s" % (
                r["x"], fmt(r["views"]), fmt(r["vpd"]), int(r["age"] or 0), (r["dur"] or 0) // 60, fmt(r["subs"]),
                fmt(r["med"]), r["title"][:90], r["ch"][:28], r["id"]))
        small = [r for r in scored if (r["subs"] or 1e12) < 50000 and r["x"] >= 3]
        lines.append("SMALL-CHANNEL WINS (under 50K subs, 3x+): %d" % len(small))
        lines.append("WINNER TITLE WORDS: " + ", ".join("%s(%d)" % (w, c) for w, c in words.most_common(20)))
    return dict(mode="out", items=out), lines


def mode_debug(queries, a):
    """Dump the raw shape of what YouTube sent, to fix the parser when the page layout changes."""
    res, lines = [], []
    for q in queries:
        url = ("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(q) + "&hl=en&gl=US&sp=EgIQAQ%3D%3D")
        html = get(url)
        data = initial_data(html)
        t = re.search(r"<title>(.*?)</title>", html)
        info = dict(q=q, html_len=len(html), title=t.group(1) if t else None, has_data=bool(data),
                    marker=[m.start() for m in re.finditer("ytInitialData", html)][:5])
        if data:
            found = walk(data, {"videoRenderer", "lockupViewModel", "gridVideoRenderer"})
            info["kinds"] = dict(Counter(k for k, _ in found))
            for kind in ("videoRenderer", "lockupViewModel"):
                first = next((v for k, v in found if k == kind), None)
                if first is not None:
                    info[kind + "_keys"] = sorted(first.keys())
                    info[kind + "_raw"] = json.dumps(first)[:6000]
        else:
            info["head"] = html[:1500]
        res.append(info)
        lines.append("%s | html %d | data %s | kinds %s | title %s" % (q, len(html), bool(data), info.get("kinds"), info["title"]))
        time.sleep(0.5)
    return dict(mode="debug", items=res), lines


def velocity(result, state_path):
    """Real views/hour: compare today's view counts with the last time we saw the same video."""
    try:
        seen = json.load(open(state_path))
    except Exception:  # noqa
        seen = {}
    now = time.time()
    notes = []

    def visit(r):
        if not isinstance(r, dict) or not r.get("id") or r.get("views") is None:
            return
        old = seen.get(r["id"])
        if old and now - old[0] > 6 * 3600 and r["views"] >= old[1]:
            r["vph"] = round((r["views"] - old[1]) / ((now - old[0]) / 3600), 2)
            if r["vph"] >= 5:
                notes.append("%6.1f views/hour now | %s https://youtu.be/%s" % (r["vph"], r.get("title", "")[:80], r["id"]))
        seen[r["id"]] = [int(now), r["views"]]

    for it in result.get("items", []):
        for key in ("rows", "scored", "unscored"):
            for r in it.get(key, []) or []:
                visit(r)
    if len(seen) > 6000:
        seen = dict(sorted(seen.items(), key=lambda kv: -kv[1][0])[:6000])
    os.makedirs(os.path.dirname(state_path) or ".", exist_ok=True)
    json.dump(seen, open(state_path, "w"))
    return sorted(notes, reverse=True)[:15]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["kw", "out", "batch", "debug"])
    p.add_argument("query")
    p.add_argument("--out", default="iqvid-run")
    p.add_argument("--n", type=int, default=9, help="kw: autocomplete phrases to measure")
    p.add_argument("--fast", action="store_true", help="kw: skip the a-z and question expansion")
    p.add_argument("--pages", type=int, default=2, help="out: result pages per search")
    p.add_argument("--extra", type=int, default=3, help="out: extra autocomplete searches per topic")
    p.add_argument("--minlen", type=int, default=LONG_MIN, help="out: minimum seconds")
    p.add_argument("--channels", type=int, default=45, help="out: max channels to baseline")
    p.add_argument("--top", type=int, default=25)
    a = p.parse_args()
    queries = [q.strip() for q in a.query.split("|") if q.strip()]
    result, lines = {"kw": mode_kw, "out": mode_out, "batch": mode_batch, "debug": mode_debug}[a.mode](queries, a)
    vel = velocity(result, os.path.join(os.path.dirname(a.out) or ".", "seen.json"))
    if vel:
        lines += ["MOVING NOW (real views/hour since our last look):"] + vel
    result["when"] = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    json.dump(result, open(a.out + ".json", "w"), separators=(",", ":"))
    open(a.out + ".txt", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
