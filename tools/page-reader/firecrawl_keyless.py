#!/usr/bin/env python3
"""Page reader: Firecrawl KEYLESS (no account, no key; free, capped per IP per day).

Why (Neko Nov 26 2026, GROW head-to-head, tested live on a GitHub runner): on a YouTube watch page it returned the
FULL description plus views/likes/upload date where TinyFish fetch cut the description at ~200 characters, and it
read an Etsy search page (120K characters) that TinyFish reported as bot_blocked. It REFUSES TikTok and Instagram
tag/listing pages (HTTP 400) - use TinyFish fetch for those. The cloud sandbox cannot reach api.firecrawl.dev, so
this runs on a GitHub runner: workflow page-reader.yml.

Usage: python3 tools/page-reader/firecrawl_keyless.py URL [URL ...]   (prints markdown; exit 1 if every URL failed)
Never pass a private or signed-in URL: the page goes through Firecrawl's servers."""
import json, sys, time, urllib.request, urllib.error

MAX = 60000  # characters kept per page


def scrape(url):
    body = json.dumps({"url": url, "formats": ["markdown"]}).encode()
    req = urllib.request.Request("https://api.firecrawl.dev/v2/scrape", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            status, raw = r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:  # noqa
        return 0, "", str(e)[:300]
    try:
        j = json.loads(raw)
    except Exception:
        return status, "", raw[:300]
    return status, ((j.get("data") or {}).get("markdown")) or "", str(j.get("error") or "")[:300]


def main():
    urls = [u for u in sys.argv[1:] if u.startswith("http")]
    if not urls:
        print(__doc__)
        sys.exit(2)
    ok = 0
    for u in urls:
        t = time.time()
        status, md, err = scrape(u)
        print("################ %s" % u)
        print("HTTP %s | %.1fs | %d characters%s" % (status, time.time() - t, len(md), (" | error: " + err) if err else ""))
        if md:
            ok += 1
            print(md[:MAX])
            if len(md) > MAX:
                print("\n[cut at %d of %d characters]" % (MAX, len(md)))
        print()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
