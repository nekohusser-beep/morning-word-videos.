#!/usr/bin/env python3
"""Buffer without the connector: talks straight to api.buffer.com with a personal API key.

Key comes from the BUFFER_API_KEY environment variable (a GitHub repo secret in Actions).

  python3 tools/buffer.py list   [--days 10]
  python3 tools/buffer.py post   --channel youtube --video URL --text "..." [--title "..."]
                                 [--due 2026-10-17T05:00:00-04:00] [--privacy public|unlisted|private]
  python3 tools/buffer.py move   --id POST_ID --due 2026-10-17T05:00:00-04:00
  python3 tools/buffer.py delete --id POST_ID
"""
import argparse, datetime as dt, json, os, sys, urllib.request

API = "https://api.buffer.com"
ORG = "6acb44d6391fa2035057ed9d"
CHANNELS = {
    "youtube": "6acb490a778b240e2fd4d3a0",
    "tiktok": "6acb49be778b240e2fd4d7cc",
    "instagram": "6acb4877778b240e2fd4cfd3",
}
ET = dt.timezone(dt.timedelta(hours=-4))


def gql(query, variables=None):
    key = os.environ.get("BUFFER_API_KEY")
    if not key:
        sys.exit("BUFFER_API_KEY is not set")
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if out.get("errors"):
        sys.exit("Buffer error: " + json.dumps(out["errors"]))
    return out["data"]


def result(payload):
    if "post" in payload:
        p = payload["post"]
        print(f"OK {p['id']} {p['status']} due {p.get('dueAt')}")
        return p
    sys.exit("Buffer refused: " + payload.get("message", json.dumps(payload)))


LIST = """query($org: OrganizationId!, $start: DateTime, $end: DateTime) {
  posts(first: 50, input: {organizationId: $org,
        filter: {dueAt: {start: $start, end: $end}, status: [scheduled, sent, error, sending]},
        sort: [{field: dueAt, direction: asc}]}) {
    edges { node { id status dueAt channelService text error { message } assets { source } } }
  }
}"""

POST_FIELDS = """... on PostActionSuccess { post { id status dueAt } }
    ... on MutationError { message }"""


def cmd_list(a):
    now = dt.datetime.now(ET).replace(hour=0, minute=0, second=0, microsecond=0)
    d = gql(LIST, {"org": ORG, "start": now.isoformat(),
                   "end": (now + dt.timedelta(days=a.days)).isoformat()})
    for e in d["posts"]["edges"] or []:
        n = e["node"]
        when = dt.datetime.fromisoformat(n["dueAt"].replace("Z", "+00:00")).astimezone(ET)
        first = (n["text"] or "").splitlines()[0][:70]
        err = f"  ERROR: {n['error']['message']}" if n.get("error") else ""
        print(f"{when:%a %m/%d %I:%M %p}  {n['channelService']:<9} {n['status']:<9} {n['id']}  {first}{err}")


def cmd_post(a):
    meta = {}
    if a.channel == "youtube":
        meta = {"youtube": {"title": a.title or a.text.splitlines()[0][:100], "categoryId": "22",
                            "privacy": a.privacy, "madeForKids": False,
                            "notifySubscribers": True, "isAiGenerated": True}}
    elif a.channel == "tiktok":
        meta = {"tiktok": {"isAiGenerated": True}}
    elif a.channel == "instagram":
        meta = {"instagram": {"type": "reel", "shouldShareToFeed": True, "isAiGenerated": True}}
    inp = {
        "channelId": CHANNELS[a.channel], "text": a.text,
        "schedulingType": "automatic",
        "mode": "customScheduled" if a.due else "addToQueue",
        "assets": [{"video": {"url": a.video}}], "metadata": meta,
    }
    if a.due:
        inp["dueAt"] = a.due
    d = gql("mutation($i: CreatePostInput!) { createPost(input: $i) { " + POST_FIELDS + " } }", {"i": inp})
    result(d["createPost"])


def cmd_move(a):
    inp = {"id": a.id, "dueAt": a.due, "mode": "customScheduled", "schedulingType": "automatic"}
    d = gql("mutation($i: EditPostInput!) { editPost(input: $i) { " + POST_FIELDS + " } }", {"i": inp})
    result(d["editPost"])


def cmd_delete(a):
    d = gql("mutation($i: DeletePostInput!) { deletePost(input: $i) { "
            "... on DeletePostSuccess { id } ... on MutationError { message } } }", {"i": {"id": a.id}})
    print(d["deletePost"])


def main():
    # Command line only runs when this file is executed, never when another script imports it
    # (tools/watchdog.py imports gql and ORG from here).
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="cmd", required=True)
    l = s.add_parser("list"); l.add_argument("--days", type=int, default=10)
    c = s.add_parser("post")
    c.add_argument("--channel", choices=CHANNELS, required=True)
    c.add_argument("--video", required=True); c.add_argument("--text", required=True)
    c.add_argument("--title"); c.add_argument("--due")
    c.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    m = s.add_parser("move"); m.add_argument("--id", required=True); m.add_argument("--due", required=True)
    x = s.add_parser("delete"); x.add_argument("--id", required=True)
    a = p.parse_args()
    {"list": cmd_list, "post": cmd_post, "move": cmd_move, "delete": cmd_delete}[a.cmd](a)


if __name__ == "__main__":
    main()
