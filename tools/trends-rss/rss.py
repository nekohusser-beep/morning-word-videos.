"""Google Trends daily trending searches via the public RSS feed (no key, no pytrends 429s).
Idea from an n8n 'Google Trends -> Google Sheets' post Neko sent Nov 25 2026; rebuilt free in Python.
Writes reports/trends-rss/<YYYY-MM-DD>.json and .md, newest first, with a 'hook' flag for topics a
Blessed Prayers trend Short can answer (the GTA 6 Short pattern: viral topic -> KJV verse).
"""
import json, os, re, sys, datetime, urllib.request, xml.etree.ElementTree as ET

GEO = os.environ.get("GEO", "US")
URL = "https://trends.google.com/trending/rss?geo=" + GEO
NS = {"ht": "https://trends.google.com/trending/rss"}
FAITH = re.compile(r"\b(god|jesus|christ|bible|pray|prayer|church|pastor|pope|faith|heaven|hell|angel|"
                   r"thanksgiving|christmas|easter|advent|grief|death|died|funeral|storm|hurricane|"
                   r"tornado|flood|fire|shooting|war|anxiety|depression|sleep|lonely|cancer)\b", re.I)

def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (trends-rss; github.com/nekohusser-beep)"})
    return urllib.request.urlopen(req, timeout=30).read()

def parse(xml):
    out = []
    for it in ET.fromstring(xml).iter("item"):
        g = lambda t: (it.findtext(t, default="", namespaces=NS) or "").strip()
        news = [{"title": (n.findtext("ht:news_item_title", default="", namespaces=NS) or "").strip(),
                 "source": (n.findtext("ht:news_item_source", default="", namespaces=NS) or "").strip()}
                for n in it.findall("ht:news_item", NS)]
        text = g("title") + " " + " ".join(n["title"] for n in news)
        out.append({"query": g("title"), "traffic": g("ht:approx_traffic"), "pubDate": g("pubDate"),
                    "news": news[:3], "hook": bool(FAITH.search(text))})
    return out

def main():
    items = parse(fetch())
    day = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5))).strftime("%Y-%m-%d")
    os.makedirs("reports/trends-rss", exist_ok=True)
    base = "reports/trends-rss/" + day
    json.dump({"geo": GEO, "made_utc": datetime.datetime.utcnow().isoformat(timespec="seconds"), "items": items},
              open(base + ".json", "w"), indent=1)
    lines = ["# Google Trends %s %s (%d trending)" % (GEO, day, len(items)), "",
             "hook | query | traffic | top headline", "---|---|---|---"]
    for i in sorted(items, key=lambda x: not x["hook"]):
        h = i["news"][0]["title"] if i["news"] else ""
        lines.append("%s | %s | %s | %s" % ("YES" if i["hook"] else "", i["query"], i["traffic"], h.replace("|", "/")))
    open(base + ".md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[:40]))
    print("items=%d hooks=%d" % (len(items), sum(i["hook"] for i in items)))
    if not items:
        sys.exit(1)

if __name__ == "__main__":
    main()
