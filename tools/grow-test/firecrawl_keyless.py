#!/usr/bin/env python3
"""GROW head-to-head (Neko Nov 26 2026): Firecrawl KEYLESS (no account, no key, free daily cap per IP) on the
pages our readers struggle with. Prints raw results to the job log; nothing is committed, no secrets used.
Truth for the YouTube page: full description is 511 chars and ends near 'send this to somebody starting their day'."""
import json, sys, urllib.request, urllib.error, time

URLS = [
    ("youtube watch page", "https://www.youtube.com/watch?v=BaXcP8x1Mp8", "send this to somebody starting their day"),
    ("tiktok tag page", "https://www.tiktok.com/tag/morningprayer", "morningprayer"),
    ("etsy search page", "https://www.etsy.com/search?q=christian+t+shirt", "shirt"),
    ("instagram tag page", "https://www.instagram.com/explore/tags/morningprayer/", "morningprayer"),
    ("plain article (control)", "https://buffer.com/pricing", "scheduled posts"),
]
for name, url, needle in URLS:
    body = json.dumps({"url": url, "formats": ["markdown"]}).encode()
    req = urllib.request.Request("https://api.firecrawl.dev/v2/scrape", data=body,
                                 headers={"Content-Type": "application/json"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            status, raw = r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:  # noqa
        status, raw = 0, str(e)
    dt = time.time() - t
    md = ""
    try:
        j = json.loads(raw)
        md = ((j.get("data") or {}).get("markdown")) or ""
        err = j.get("error") or ""
    except Exception:
        err = raw[:300]
    print("=== %s | %s" % (name, url))
    print("HTTP %s | %.1fs | markdown %d chars | needle %r found: %s | error: %s" % (
        status, dt, len(md), needle, needle.lower() in md.lower(), str(err)[:300]))
    print("FIRST 500: " + md[:500].replace("\n", " | "))
    print()
