#!/usr/bin/env python3
"""Pull PUBLIC-DOMAIN / CC0 sacred ceiling art (putti, angels, cloud skies) from Wikimedia Commons for the sung-Psalm Shorts.
License gate: only LicenseShortName that starts with 'Public domain', 'PD' or 'CC0'. CC BY / CC BY-SA photos are skipped on purpose
(a photo of a ceiling can carry the photographer's copyright, and share-alike would attach to our video).
Writes out/img/<n>.jpg (about 3000 px wide) and out/manifest.json (title, artist, license, page url, size).
Usage: fetch.py [per_query=30] [min_width=2400]"""
import json, re, sys, time, urllib.parse, urllib.request, os, html

UA = "KingdomImpactVideos/1.0 (neko.husser@gmail.com; sacred-art Shorts)"
API = "https://commons.wikimedia.org/w/api.php"
PER = int(sys.argv[1]) if len(sys.argv) > 1 else 30
MINW = int(sys.argv[2]) if len(sys.argv) > 2 else 2400
QUERIES = [
    "putti ceiling fresco", "cherubs clouds baroque painting", "Tiepolo ceiling fresco angels", "Correggio Assumption of the Virgin cupola",
    "Veronese ceiling Venice", "Murillo Immaculate Conception cherubs", "Bouguereau angels", "baroque ceiling heaven angels clouds",
    "Raphael Sistine Madonna putti", "Gaulli Triumph of the Name of Jesus", "Pozzo ceiling Sant'Ignazio", "Assumption of the Virgin baroque painting",
    "Tintoretto Paradise Venice", "angels music concert heaven painting", "Michelangelo Sistine Chapel ceiling angels", "Coronation of the Virgin angels painting",
]
OK_LIC = re.compile(r"^(public domain|pd\b|pd-|cc0)", re.I)

def call(params, tries=4):
    url = API + "?" + urllib.parse.urlencode(params)
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:
            time.sleep(2 * (t + 1))
    return {}

def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

def pick(page):
    ii = (page.get("imageinfo") or [None])[0]
    if not ii: return None
    if ii.get("mime") != "image/jpeg": return None
    if (ii.get("width") or 0) < MINW: return None
    md = ii.get("extmetadata") or {}
    lic = clean((md.get("LicenseShortName") or {}).get("value", ""))
    if not OK_LIC.match(lic): return None
    if (md.get("Restrictions") or {}).get("value"): return None
    return {"title": page["title"].replace("File:", ""), "artist": clean((md.get("Artist") or {}).get("value", ""))[:120],
            "license": lic, "page": ii.get("descriptionurl"), "w": ii["width"], "h": ii["height"], "thumb": ii.get("thumburl"), "q": None}

def main():
    os.makedirs("out/img", exist_ok=True)
    seen, rows = set(), []
    for q in QUERIES:
        d = call({"action": "query", "format": "json", "generator": "search", "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6,
                  "gsrlimit": PER, "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 3000})
        n0 = len(rows)
        for p in (d.get("query", {}).get("pages", {}) or {}).values():
            r = pick(p)
            if r and r["title"] not in seen and r["thumb"]:
                seen.add(r["title"]); r["q"] = q; rows.append(r)
        print(f"{q!r}: +{len(rows)-n0}", flush=True)
    for i, r in enumerate(rows):
        fn = f"out/img/{i:03d}.jpg"
        for t in range(4):
            try:
                req = urllib.request.Request(r["thumb"], headers={"User-Agent": UA})
                open(fn, "wb").write(urllib.request.urlopen(req, timeout=120).read()); r["file"] = fn; break
            except Exception as e:
                time.sleep(3 * (t + 1))
        else:
            r["file"] = None
        time.sleep(0.4)
    rows = [r for r in rows if r.get("file")]
    json.dump(rows, open("out/manifest.json", "w"), indent=1)
    print("TOTAL", len(rows))

if __name__ == "__main__":
    main()
