#!/usr/bin/env python3
"""Drive a self-hosted OpenShorts through its REST API and time every stage.

Usage: drive.py <video> <outdir> [--no-captions] [--target-clips N] [--api http://127.0.0.1:8000]
Writes into <outdir>: timeline.tsv (seconds since submit + log line), status.json,
summary.json, clip files. Pure stdlib so it runs on a bare runner.
"""
import argparse, json, os, sys, time, urllib.request, urllib.error


def call(method, url, body=None, raw=None, headers=None, timeout=300):
    h = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    if raw is not None:
        data = raw
        h["Content-Type"] = "application/octet-stream"
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {"detail": str(e.reason)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("outdir")
    ap.add_argument("--api", default="http://127.0.0.1:8000")
    ap.add_argument("--no-captions", action="store_true")
    ap.add_argument("--target-clips", type=int, default=0)
    ap.add_argument("--max-wait", type=int, default=7200)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    api = a.api.rstrip("/")
    summary = {"video": os.path.basename(a.video), "bytes": os.path.getsize(a.video)}

    t = time.time()
    st, slot = call("POST", api + "/api/uploads", {"filename": os.path.basename(a.video)})
    if st >= 400:
        sys.exit(f"upload slot failed {st} {slot}")
    with open(a.video, "rb") as f:
        st, put = call("PUT", f"{api}/api/uploads/{slot['upload_id']}", raw=f.read(), timeout=1800)
    if st >= 400:
        sys.exit(f"upload failed {st} {put}")
    summary["upload_seconds"] = round(time.time() - t, 1)
    summary["source_duration_seconds"] = put.get("duration_seconds")
    print("uploaded", put, flush=True)

    body = {"upload_id": slot["upload_id"], "acknowledged": True}
    if a.no_captions:
        body["captions"] = False
    if a.target_clips:
        body["target_clips"] = a.target_clips
    summary["request"] = body
    submit = time.time()
    st, job = call("POST", api + "/api/process", body)
    if st >= 400:
        sys.exit(f"process failed {st} {job}")
    job_id = job["job_id"]
    summary["job_id"] = job_id
    print("job", job_id, flush=True)

    seen = 0
    rows = []
    payload = {}
    state = None
    while time.time() - submit < a.max_wait:
        st, payload = call("GET", f"{api}/api/status/{job_id}")
        if st >= 400:
            sys.exit(f"status failed {st} {payload}")
        logs = payload.get("logs") or []
        times = payload.get("log_times") or []
        for i in range(seen, len(logs)):
            ts = times[i] if i < len(times) and times[i] else time.time()
            rows.append((round(ts - submit, 1), logs[i]))
            print(f"[{rows[-1][0]:>7}s] {logs[i]}", flush=True)
        seen = len(logs)
        state = payload.get("status")
        if state in ("completed", "failed"):
            break
        time.sleep(5)
    summary["final_status"] = state
    summary["wall_seconds_submit_to_end"] = round(time.time() - submit, 1)

    with open(os.path.join(a.outdir, "timeline.tsv"), "w") as f:
        for s, line in rows:
            f.write(f"{s}\t{line}\n")
    with open(os.path.join(a.outdir, "status.json"), "w") as f:
        json.dump(payload, f, indent=1)

    clips = ((payload.get("result") or {}).get("clips")) or []
    summary["clip_count"] = len(clips)
    summary["clips"] = []
    for i, c in enumerate(clips):
        url = c.get("download_url") or c.get("video_url") or ""
        if url.startswith("/"):
            url = api + url
        name = f"clip{i + 1:02d}.mp4"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=600) as r, open(os.path.join(a.outdir, name), "wb") as out:
                out.write(r.read())
            ok = True
        except Exception as e:
            ok = False
            print("download failed", url, e, flush=True)
        summary["clips"].append({"file": name if ok else None,
                                 "title": c.get("title") or c.get("video_title_for_youtube_short"),
                                 "start": c.get("start"), "end": c.get("end")})
    with open(os.path.join(a.outdir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1), flush=True)
    sys.exit(0 if state == "completed" else 1)


if __name__ == "__main__":
    main()
