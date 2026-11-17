#!/usr/bin/env python3
"""curator_finder.py - our own PlaylistSupply. Finds Spotify playlists in our genres that are open to
submissions RIGHT NOW, already bot-checked, with the curator's price, share rate and real listeners.

How PlaylistSupply does it (taken apart Nov 15 2026): a scraped index of Spotify playlists + curator
contacts, and "PlaylistVet" = checking a playlist shows up in real artists' "Discovered On" data.
How we do it free: artist.tools publishes, per genre and refreshed daily, the playlists that accept
submissions, already screened for bots (their fraud data), each linked to the curator's SubmitLink
page. SubmitLink shows the curator's price, how often they actually add songs (share rate) and real
listener counts. We pull both, rank by real listeners per dollar, and flag thin-listener playlists.
Needs no account, no key. Spotify's own API is closed to us (needs Premium since Feb 2026).

Run: python3 curator_finder.py gospel christian reggae afrobeats   (default list below)
Out: reports/curators/<date>.md and .csv
"""
import csv, datetime as dt, html, os, re, sys, time, urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "reports", "curators")
DEFAULT = ["gospel", "christian", "reggae", "afrobeats", "worship", "soul", "r-b"]


def get(url):
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            err = e
            time.sleep(2 * (i + 1))
    print("  fetch failed:", url, err)
    return ""


def num(s):
    s = (s or "").replace(",", "").replace("+", "").strip().upper()
    m = re.match(r"([\d.]+)\s*([KM]?)", s)
    if not m:
        return 0
    return int(float(m.group(1)) * {"": 1, "K": 1000, "M": 1000000}[m.group(2)])


def text(s):
    s = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))


def genre_rows(genre):
    page = get("https://www.artist.tools/submit/%s" % genre)
    rows = []
    for li in re.findall(r'(?s)<li class="pl-(?:tile|rank)[^"]*".*?</li>', page):
        slug = re.search(r"submitlink\.io/c/([A-Za-z0-9_\-]+)", li)
        pid = re.search(r'data-playlist-id="([A-Za-z0-9]{22})"', li)
        title = re.search(r'(?s)<h3 class="pl-title"[^>]*>.*?<a[^>]*>(.*?)</a>', li)
        t = text(li)
        fol = re.search(r"([\d.,]+[KM]?)\+?\s*followers", t)
        lis = re.search(r"([\d.,]+[KM]?)\+?\s*listeners", t)
        grow = re.search(r"\+([\d.,]+[KM]?)/day", t)
        fresh = re.search(r"new music (today|this week|\w+ ago|[^·|]{0,20})", t)
        if not (slug and pid):
            continue
        rows.append({"genre": genre, "playlist": html.unescape(title.group(1)).strip() if title else "",
                     "playlist_url": "https://open.spotify.com/playlist/" + pid.group(1),
                     "followers": num(fol.group(1) if fol else ""), "listeners": num(lis.group(1) if lis else ""),
                     "growth_per_day": num(grow.group(1)) if grow else 0,
                     "updated": ("new music " + fresh.group(1).strip()) if fresh else "",
                     "curator": slug.group(1), "accepting": "Accepting submissions" in li})
    return rows


def curator_info(slug, cache):
    if slug in cache:
        return cache[slug]
    t = text(get("https://submitlink.io/c/%s" % slug))
    price = re.search(r"submit for \$\s?(\d+(?:\.\d+)?)", t, re.I)
    free = re.search(r"submit for free|free submission", t, re.I)
    share = re.search(r"Share Rate\s+(\d+)\s*%", t, re.I)
    name = re.search(r"Submit Music to (.*?) \| Spotify Curator", t)
    tl = re.search(r"Playlist Listeners\s+([\d,.]+[KM]?)", t)
    info = {"curator_name": name.group(1).strip() if name else slug,
            "price": 0.0 if (free and not price) else (float(price.group(1)) if price else None),
            "share_rate": int(share.group(1)) if share else None,
            "curator_listeners": num(tl.group(1)) if tl else 0,
            "submit_url": "https://submitlink.io/c/%s" % slug}
    cache[slug] = info
    time.sleep(0.7)
    return info


def risk(r):
    if r["followers"] >= 2000 and r["listeners"] and r["listeners"] / r["followers"] < 0.004:
        return "thin listeners (check before paying)"
    return ""


def main():
    genres = sys.argv[1:] or DEFAULT
    cache, rows, seen = {}, [], set()
    for g in genres:
        got = genre_rows(g)
        print("%s: %d playlists" % (g, len(got)))
        for r in got:
            if r["playlist_url"] in seen:
                continue
            seen.add(r["playlist_url"])
            r.update(curator_info(r["curator"], cache))
            r["risk"] = risk(r)
            p, sh = r["price"], (r["share_rate"] or 0) / 100.0
            # expected real listeners reached per dollar = listeners x chance they add you / price
            r["listeners_per_dollar"] = round(r["listeners"] * sh / p, 1) if p else (round(r["listeners"] * sh, 1) if p == 0 else "")
            rows.append(r)
    def key(r):
        free = r["price"] == 0
        return (not free, bool(r["risk"]), -(r["listeners_per_dollar"] or 0) if r["listeners_per_dollar"] != "" else 0)
    rows.sort(key=key)
    os.makedirs(OUT, exist_ok=True)
    day = dt.date.today().isoformat()
    cols = ["genre", "playlist", "followers", "listeners", "growth_per_day", "updated", "curator_name", "price", "share_rate",
            "listeners_per_dollar", "risk", "submit_url", "playlist_url"]
    with open(os.path.join(OUT, day + ".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    free = [r for r in rows if r["price"] == 0]
    lines = ["# Curators open right now (%s) - genres: %s" % (day, ", ".join(genres)), "",
             "%d playlists from %d curators. Free: %d. Bot-screened by artist.tools; listener counts from SubmitLink. Reach per $ = listeners x how often the curator adds songs / price (best value first)."
             % (len(rows), len(cache), len(free)), "",
             "| # | Genre | Playlist | Followers | Listeners | Growing | Price | Adds songs | Reach per $ | Note | Submit |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        price = "free" if r["price"] == 0 else ("$%g" % r["price"] if r["price"] is not None else "?")
        share = "%d%%" % r["share_rate"] if r["share_rate"] is not None else "?"
        lines.append("| %d | %s | [%s](%s) | %s | %s | %s | %s | %s | %s | %s | [submit](%s) |" % (
            i, r["genre"], r["playlist"].replace("|", "/"), r["playlist_url"], f"{r['followers']:,}",
            f"{r['listeners']:,}", ("+%d/day" % r["growth_per_day"]) if r["growth_per_day"] else "", price, share, r["listeners_per_dollar"], r["risk"], r["submit_url"]))
    open(os.path.join(OUT, day + ".md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("wrote reports/curators/%s.md (%d rows)" % (day, len(rows)))
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
