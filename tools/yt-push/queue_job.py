#!/usr/bin/env python3
"""Queue an IQ Vid package for yt-push in one line (run from either repo).

  python3 tools/yt-push/queue_job.py VIDEO_ID --pack <path to content_pack.json> [--pick B]
      [--playlist PL...] [--comment "text"] [--captions <path to captions.srt>]
      [--title "..."] [--tags "a,b,c"] [--localized es="..." --localized fr="..."]

The pack's title, description (with chapters) and tags are copied INTO the job, and the caption file
is copied beside it, so the job works from this public repo even when the pack lives in kingdom-brain.
Writes tools/yt-push/queue/<video>-<time>.json here. Commit + push: the yt-push workflow applies it.
"""
import argparse, json, os, shutil, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import yt_push  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("video_id")
ap.add_argument("--pack"); ap.add_argument("--pick", default="A")
ap.add_argument("--title"); ap.add_argument("--description"); ap.add_argument("--tags")
ap.add_argument("--playlist", action="append"); ap.add_argument("--comment")
ap.add_argument("--captions"); ap.add_argument("--captions-lang", default="en")
ap.add_argument("--localized", action="append", help='lang="title"')
ap.add_argument("--thumbnail", help="JPG/PNG under 2 MB")
ap.add_argument("--ship", action="store_true", help="commit + push now, wait for the run, print the result")
a = ap.parse_args()

job = {"video_id": a.video_id}
if a.pack:
    pack_abs = os.path.abspath(a.pack)
    rel = os.path.relpath(pack_abs, REPO)
    want, problems = yt_push.resolve_job({"video_id": a.video_id, "pack": rel, "title_pick": a.pick})
    bad = yt_push.blocking(problems)
    if bad:
        sys.exit("NOT QUEUED: " + "; ".join(bad))
    for k in ("title", "description", "tags"):
        if k in want:
            job[k] = want[k]
    job["source_pack"] = os.path.basename(os.path.dirname(os.path.dirname(pack_abs))) + "/pack/content_pack.json"
if a.title: job["title"] = a.title
if a.description: job["description"] = a.description
if a.tags: job["tags"] = [t.strip() for t in a.tags.split(",") if t.strip()]
if a.playlist: job["playlist_ids"] = a.playlist
if a.comment: job["comment"] = a.comment
if a.localized:
    job["localized_titles"] = dict(x.split("=", 1) for x in a.localized)
stamp = time.strftime("%Y%m%d-%H%M%S")
qdir = os.path.join(HERE, "queue")
os.makedirs(qdir, exist_ok=True)
if a.captions:
    cap_dir = os.path.join(HERE, "captions"); os.makedirs(cap_dir, exist_ok=True)
    dest = os.path.join(cap_dir, "%s-%s.srt" % (a.video_id, stamp))
    shutil.copyfile(a.captions, dest)
    job["captions_file"], job["captions_lang"] = os.path.relpath(dest, REPO), a.captions_lang
if a.thumbnail:
    th_dir = os.path.join(HERE, "thumbs"); os.makedirs(th_dir, exist_ok=True)
    ext = os.path.splitext(a.thumbnail)[1].lower() or ".jpg"
    dest = os.path.join(th_dir, "%s-%s%s" % (a.video_id, stamp, ext))
    shutil.copyfile(a.thumbnail, dest)
    job["thumbnail_file"] = os.path.relpath(dest, REPO)
want, problems = yt_push.resolve_job(job)
bad = yt_push.blocking(problems)
if bad:
    sys.exit("NOT QUEUED: " + "; ".join(bad))
path = os.path.join(qdir, "%s-%s.json" % (a.video_id, stamp))
json.dump(job, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
rel = os.path.relpath(path, REPO)
print(rel)

if a.ship:
    import subprocess
    R = "nekohusser-beep/morning-word-videos."
    def sh(*c):
        return subprocess.run(c, cwd=REPO, capture_output=True, text=True)
    sh("git", "add", "-A", "tools/yt-push")
    sh("git", "commit", "-q", "-m", "yt-push job %s" % a.video_id)
    for _ in range(5):
        sh("git", "fetch", "-q", "--depth=20", "origin", "main"); sh("git", "rebase", "-q", "origin/main")
        if sh("git", "-c", "push.negotiate=true", "push", "-q", "origin", "HEAD:main").returncode == 0:
            break
        time.sleep(3)
    head = sh("git", "rev-parse", "HEAD").stdout.strip()
    print("pushed", head[:7], "- waiting for the yt-push run...")
    run_id, deadline = None, time.time() + 600
    while time.time() < deadline:
        time.sleep(10)
        q = sh("gh", "api", "repos/%s/actions/workflows/yt-push.yml/runs?per_page=5" % R,
               "--jq", '.workflow_runs[]|select(.head_sha=="%s")|[.id,.status,.conclusion]|@tsv' % head).stdout.split()
        if len(q) >= 2:
            run_id = q[0]
            if q[1] == "completed":
                print("run", run_id, q[2] if len(q) > 2 else "")
                break
    sh("git", "fetch", "-q", "--depth=20", "origin", "main"); sh("git", "rebase", "-q", "origin/main")
    import glob
    done = sorted(glob.glob(os.path.join(qdir, "done", os.path.basename(path)[:-5] + "-*.json")))
    if done:
        r = json.load(open(done[-1], encoding="utf-8"))["results"]
        for x in r:
            print("changed:", ", ".join(x["changed"]) or "nothing")
            if x["skipped"]: print("skipped:", "; ".join(x["skipped"]))
            if x["errors"]: print("ERRORS:", "; ".join(x["errors"]))
    else:
        print("no result yet; see reports/yt-push/run-%s-apply.txt" % run_id)
