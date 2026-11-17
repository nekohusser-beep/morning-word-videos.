#!/usr/bin/env python3
"""Slot watchdog for Blessed Prayers: reads the Buffer queue and pushes a phone alert (ntfy) for any empty slot.

Needs env BUFFER_API_KEY (same secret tools/buffer.py uses) and NTFY_TOPIC (long random string, repo secret).

  python3 tools/watchdog.py                 # real run (the GitHub workflow runs this every 30 min)
  python3 tools/watchdog.py --test          # send one test alert to the phone
  python3 tools/watchdog.py --fixture posts.json --now 2026-10-28T03:51:00-04:00 --dry-run   # offline test

Slot map: Derrick Mon-Fri 5:00 AM ET; cards 7:00 AM, 5:00 PM, 9:00 PM ET every day; on YouTube, TikTok, Instagram.
A slot is filled on a channel only by a post that is scheduled, sending or sent (drafts do not count).
Alert marks: 24 h, 6 h and 2 h before an empty slot, then 15 min and 2 h after a slot that did not go out.
"""
import argparse, datetime as dt, json, os, sys, urllib.request
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ET = ZoneInfo("America/New_York")
CHANNELS = ["youtube", "tiktok", "instagram"]
SLOTS = [  # label, hour, minute, weekdays (0 = Monday)
    ("Derrick 5 AM", 5, 0, range(0, 5)),
    ("Card 7 AM", 7, 0, range(0, 7)),
    ("Card 5 PM", 17, 0, range(0, 7)),
    ("Card 9 PM", 21, 0, range(0, 7)),
]
MARKS = (24, 6, 2, -0.25, -2.0)   # hours until the slot when an alert may fire (negative = after it)
WINDOW = 0.5                      # the job runs every 30 min, so each mark fires about once
LOOKAHEAD = 48                    # hours of queue shown in the log grid
TOL = dt.timedelta(minutes=20)    # a post counts for a slot if it is due within 20 min of it
BEFORE = {"scheduled", "sending", "sent"}
AFTER = {"sent", "sending"}       # after the slot time, a post still "scheduled" did not go out
CAP = 10                          # Buffer free plan: scheduled posts per channel
CLICK = "https://publish.buffer.com/"

LIST = """query($org: OrganizationId!, $start: DateTime, $end: DateTime) {
  posts(first: 100, input: {organizationId: $org,
        filter: {dueAt: {start: $start, end: $end}, status: [scheduled, sent, error, sending]},
        sort: [{field: dueAt, direction: asc}]}) {
    edges { node { id status dueAt channelService } }
  }
}"""
QUEUED = """query($org: OrganizationId!) {
  posts(first: 100, input: {organizationId: $org, filter: {status: [scheduled]}}) {
    edges { node { id channelService } }
  }
}"""


def parse(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def fetch(now):
    import buffer as B  # tools/buffer.py: api.buffer.com with BUFFER_API_KEY
    start = (now - dt.timedelta(hours=4)).astimezone(dt.timezone.utc).isoformat()
    end = (now + dt.timedelta(hours=LOOKAHEAD + 1)).astimezone(dt.timezone.utc).isoformat()
    d = B.gql(LIST, {"org": B.ORG, "start": start, "end": end})
    posts = [e["node"] for e in (d["posts"]["edges"] or [])]
    q = B.gql(QUEUED, {"org": B.ORG})
    queued = {}
    for e in (q["posts"]["edges"] or []):
        c = (e["node"]["channelService"] or "").lower()
        queued[c] = queued.get(c, 0) + 1
    return posts, queued


def load_fixture(path):
    data = json.load(open(path))
    posts = data["posts"] if isinstance(data, dict) else data
    queued = {}
    for p in posts:
        if p["status"] == "scheduled":
            c = p["channelService"].lower()
            queued[c] = queued.get(c, 0) + 1
    return posts, queued


def slots_around(now):
    out = []
    today = now.astimezone(ET).date()
    for off in range(-1, 4):
        d = today + dt.timedelta(days=off)
        for label, h, m, days in SLOTS:
            if d.weekday() in days:
                out.append((label, dt.datetime(d.year, d.month, d.day, h, m, tzinfo=ET)))
    return sorted(out, key=lambda s: s[1])


def status_for(posts, channel, slot_dt):
    best = None
    for p in posts:
        if (p.get("channelService") or "").lower() != channel or not p.get("dueAt"):
            continue
        if abs(parse(p["dueAt"]) - slot_dt) <= TOL:
            if best is None or p["status"] in ("sent", "sending"):
                best = p["status"]
    return best


def fmt_gap(h):
    m = int(round(abs(h) * 60))
    return f"{m // 60}h {m % 60:02d}m"


def check(posts, queued, now):
    alerts, grid = [], []
    for label, slot_dt in slots_around(now):
        h = (slot_dt - now).total_seconds() / 3600
        if h < -3 or h > LOOKAHEAD:
            continue
        st = {c: status_for(posts, c, slot_dt) for c in CHANNELS}
        grid.append((slot_dt, label, h, st))
        for mark in MARKS:
            if not (mark - WINDOW < h <= mark):
                continue
            ok = AFTER if mark <= 0 else BEFORE
            bad = [c for c in CHANNELS if st[c] not in ok]
            if not bad:
                continue
            when = f"{slot_dt:%a %b %d %-I:%M %p} ET"
            if mark <= 0:
                why = ", ".join(f"{c} ({st[c] or 'nothing queued'})" for c in bad)
                alerts.append((5, "rotating_light", f"SLOT MISSED: {label}",
                               f"{when}, {fmt_gap(h)} ago. Did not go out on {why}."))
            else:
                pr = {24: 3, 6: 4, 2: 5}[mark]
                alerts.append((pr, "warning", f"SLOT EMPTY in {fmt_gap(h)}: {label}",
                               f"{when}. Nothing queued on {', '.join(bad)}."))
    return alerts, grid


def print_grid(grid, queued):
    print("slot (ET)                        left   " + "  ".join(f"{c[:3]:<9}" for c in CHANNELS))
    for slot_dt, label, h, st in grid:
        cells = "  ".join(f"{(st[c] or 'EMPTY'):<9}" for c in CHANNELS)
        print(f"{slot_dt:%a %m/%d %I:%M %p} {label:<13} {h:6.1f}h  {cells}")
    print("scheduled per channel:", {c: f"{queued.get(c, 0)}/{CAP}" for c in CHANNELS})


def ntfy(priority, tags, title, body):
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        sys.exit("NTFY_TOPIC is not set")
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}", data=body.encode("utf-8"),
        headers={"Title": title, "Priority": str(priority), "Tags": tags, "Click": CLICK})
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fixture")
    ap.add_argument("--now")
    a = ap.parse_args()
    now = parse(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    if a.now and now.tzinfo is None:
        now = now.replace(tzinfo=ET)

    if a.test:
        msg = (4, "white_check_mark", "Watchdog test", "If your phone made a sound, the slot watchdog can reach you.")
        print(msg) if a.dry_run else ntfy(*msg)
        return

    posts, queued = load_fixture(a.fixture) if a.fixture else fetch(now)
    alerts, grid = check(posts, queued, now)
    print(f"now {now.astimezone(ET):%a %b %d %I:%M %p} ET, {len(posts)} posts in the window")
    print_grid(grid, queued)
    if not alerts:
        print("no alerts")
        return
    full = [f"{c} {queued.get(c, 0)}/{CAP}" for c in CHANNELS if queued.get(c, 0) >= CAP]
    extra = []
    if full:
        extra.append("Queue is full (" + ", ".join(full) + "): add it after the next post goes out.")
    if not posts:
        extra.append("Buffer returned 0 posts for this window: empty queue or an API problem.")
    pr = max(x[0] for x in alerts)
    tags = alerts[0][1] if len(alerts) == 1 else ("rotating_light" if pr == 5 else "warning")
    title = alerts[0][2] if len(alerts) == 1 else f"{len(alerts)} slot problems"
    body = "\n".join([x[3] if len(alerts) == 1 else f"{x[2]}: {x[3]}" for x in alerts] + extra)
    print(f"ALERT priority {pr}: {title}\n{body}")
    if not a.dry_run:
        ntfy(pr, tags, title, body)


if __name__ == "__main__":
    main()
