#!/usr/bin/env python3
"""Feeder robot: keeps every Buffer channel topped up from the queue, no laptop, no Claude.

Queue = one JSON file per video in queue/ready/  (see queue/README.md for the format).
Each run:
  1. counts what is already scheduled per channel in Buffer
  2. posts the next ready items (soonest due first) to every channel that has room (CAP per channel)
  3. moves an item to queue/posted/ once all its channels are in, with the Buffer post ids
  4. moves items whose due time already passed to queue/stale/
  5. prints a stock report; LOW STOCK when fewer than LOW days of long videos are left

  python3 tools/feeder.py [--dry-run]
Env: BUFFER_API_KEY (secret), CAP (default 10 = Buffer free), LOW (default 3)
"""
import argparse, datetime as dt, glob, json, os, shutil, sys
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(__file__))
from buffer import gql, ORG, CHANNELS, POST_FIELDS  # noqa: E402

ET = ZoneInfo("America/New_York")
CAP = int(os.environ.get("CAP", "10"))
LOW = int(os.environ.get("LOW", "3"))
EXTRA = "queue/channels.json"  # optional extra channels, e.g. {"facebook": "<buffer channel id>"}
if os.path.exists(EXTRA):
    CHANNELS.update(json.load(open(EXTRA)))

COUNT = """query($org: OrganizationId!, $ch: [ChannelId!]) {
  posts(first: 100, input: {organizationId: $org, filter: {channelIds: $ch, status: [scheduled]}}) {
    edges { node { id } } } }"""


def scheduled(ch_id):
    d = gql(COUNT, {"org": ORG, "ch": [ch_id]})
    return len(d["posts"]["edges"] or [])


def meta_for(name, c):
    if name == "youtube":
        return {"youtube": {"title": c.get("title") or c["text"].splitlines()[0][:100], "categoryId": "22",
                            "privacy": "public", "madeForKids": False, "notifySubscribers": True,
                            "isAiGenerated": True}}
    if name == "tiktok":
        return {"tiktok": {"isAiGenerated": True}}
    if name == "instagram":
        return {"instagram": {"type": "reel", "shouldShareToFeed": True, "isAiGenerated": True}}
    if name == "facebook":
        return {"facebook": {"type": "reel"}}
    return {}


def post(name, item, c):
    inp = {"channelId": CHANNELS[name], "text": c["text"], "schedulingType": "automatic",
           "mode": "customScheduled", "dueAt": item["due"],
           "assets": [{"video": {"url": c.get("video", item["video"])}}], "metadata": meta_for(name, c)}
    d = gql("mutation($i: CreatePostInput!) { createPost(input: $i) { " + POST_FIELDS + " } }", {"i": inp})
    r = d["createPost"]
    if "post" not in r:
        raise RuntimeError(r.get("message", json.dumps(r)))
    return r["post"]["id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    for d in ("queue/ready", "queue/posted", "queue/stale"):
        os.makedirs(d, exist_ok=True)
    now = dt.datetime.now(ET)
    room = {n: CAP - scheduled(i) for n, i in CHANNELS.items()}
    print("room per channel:", room)
    files = []
    for f in glob.glob("queue/ready/*.json"):
        it = json.load(open(f))
        files.append((dt.datetime.fromisoformat(it["due"]), f, it))
    files.sort()
    for due, f, it in files:
        if due <= now + dt.timedelta(minutes=20):
            print("STALE", f)
            if not a.dry_run:
                shutil.move(f, f.replace("queue/ready/", "queue/stale/"))
            continue
        done = it.setdefault("posted", {})
        for name, c in it["channels"].items():
            if name in done or name not in CHANNELS or room.get(name, 0) <= 0:
                continue
            if a.dry_run:
                print("WOULD POST", name, os.path.basename(f), it["due"])
            else:
                try:
                    done[name] = post(name, it, c)
                    print("POSTED", name, os.path.basename(f), it["due"], done[name])
                except Exception as e:  # keep going; next run retries this channel
                    print("FAILED", name, os.path.basename(f), e)
                    continue
            room[name] -= 1
        if not a.dry_run:
            want = [n for n in it["channels"] if n in CHANNELS]
            if all(n in done for n in want):
                json.dump(it, open(f.replace("queue/ready/", "queue/posted/"), "w"), indent=1)
                os.remove(f)
            else:
                json.dump(it, open(f, "w"), indent=1)
    left = [json.load(open(f)) for f in glob.glob("queue/ready/*.json")]
    longs = [x for x in left if x.get("kind") == "long"]
    shorts = [x for x in left if x.get("kind") != "long"]
    days_long = len(longs) / 2  # 2 long videos a day (5 AM + 8:30 PM)
    days_short = len(shorts) / 3  # 3 Shorts a day
    print(f"STOCK: {len(longs)} long ({days_long:.1f} days), {len(shorts)} shorts ({days_short:.1f} days)")
    if min(days_long, days_short) < LOW:
        print("LOW STOCK")
        open("low_stock.txt", "w").write(f"Blessed Prayers stock low: {len(longs)} long videos, {len(shorts)} Shorts left")


if __name__ == "__main__":
    main()
