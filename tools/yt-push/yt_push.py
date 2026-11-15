#!/usr/bin/env python3
"""yt_push.py - our own Zapier for YouTube. Pushes IQ Vid's SEO onto Blessed Prayers videos.

What Zapier did for us (Oct 29 2026): YouTube Data API writes through Neko's connected Google
account - titles, tags, descriptions - 2 Zapier tasks per call, 100 tasks a month, then a paywall.
This does the same jobs with no task limit and no monthly bill: stdlib Python on GitHub Actions,
zero Claude/LLM calls.

HOW IT RUNS
  Drop a job file into tools/yt-push/queue/ and push. The workflow (.github/workflows/yt-push.yml)
  applies it, saves the old metadata for rollback, re-reads the video to prove the change, then
  moves the job to queue/done/ with the result written inside it.

JOB FILE (every field optional except video_id; a field left out is never touched)
  {
    "video_id": "abc123",
    "pack": "projects/<p>/pack/content_pack.json",   IQ Vid output: fills title/description/tags
    "title_pick": "A",                                which IQ Vid title (A or B), default A
    "title": "...",                                   overrides the pack
    "description": "...",
    "tags": ["kw", "..."],
    "category_id": "29",
    "default_language": "en",
    "localized_titles": {"es": "..."},                only languages the video already has
    "playlist_ids": ["PL..."],                        added if not already in it
    "comment": "...",                                 posted as the channel (YouTube's API cannot pin)
    "captions_file": "projects/<p>/pack/captions.srt",
    "captions_lang": "en",
    "captions_name": "English"
  }

MODES
  check   which secrets exist and whether a saved sign-in works. No writes.
  dry     shows exactly what each queued job would change. Read-only.
  apply   writes every queued job. Default when the workflow fires on a push.
  verify  re-reads the videos in queue/done/ from the last 7 days and compares.
  signin  one-time Google sign-in by device code; the sign-in is saved encrypted so later runs
          need no tap.

Exit codes: 0 ok / nothing queued, 1 a job failed, 2 missing credentials.
"""
import base64
import datetime as dt
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
QUEUE = os.path.join(HERE, "queue")
DONE = os.path.join(QUEUE, "done")
TOKEN_FILE = os.path.join(HERE, "signin.enc")
REPORTS = os.path.join(REPO, "reports", "yt-push")
ROLLBACK = os.path.join(REPORTS, "rollback")
API = "https://www.googleapis.com/youtube/v3"
UPLOAD_API = "https://www.googleapis.com/upload/youtube/v3"
CHANNEL_ID = "UCaKI8Xsi-MHu78UnJTY1xpg"
# force-ssl covers videos.update, playlistItems, comments and captions with one consent.
SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
MAX_TITLE, MAX_DESC, MAX_TAGS = 100, 5000, 500

SETUP_TEXT = """\
ONE-TIME SETUP (Google credentials are Neko-only, his rule):
  1. console.cloud.google.com > the project that holds the YouTube Data API key
     > Google Auth Platform: User type External, add blessedprayers4 as a Test user, then Publish app
     (In production) so the sign-in never expires; no Google review needed for our own channel.
  2. Clients > Create client > "TV and Limited Input devices". Copy Client ID and Client secret.
  3. github.com/nekohusser-beep/morning-word-videos. > Settings > Secrets and variables > Actions:
     New repository secret YT_CLIENT_ID, then YT_CLIENT_SECRET.
  4. Run the yt-push workflow with mode signin. It prints a code: open google.com/device on the
     phone, type it, pick Blessed Prayers, tap Allow ("not verified" screen: Continue).
That sign-in is saved encrypted; every later push runs with no taps.
"""


# ------------------------------------------------------------------ http
def http(method, url, data=None, headers=None, form=False, raw=None):
    h = dict(headers or {})
    body = raw
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            h["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            h["Content-Type"] = "application/json"
    for attempt in range(3):
        req = urllib.request.Request(url, data=body, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                b = r.read()
                return r.status, (json.loads(b) if b else {})
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "replace")
            if e.code in (500, 502, 503, 504) and attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            try:
                return e.code, json.loads(txt)
            except Exception:
                return e.code, {"raw": txt[:500]}
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
                continue
            return 0, {"error": str(e)[:300]}


class YT:
    def __init__(self, key=None, token=None):
        self.key, self.token = key, token

    def _h(self):
        return {"Authorization": "Bearer " + self.token} if self.token else {}

    def _u(self, path, params, upload=False):
        p = dict(params)
        if not self.token:
            p["key"] = self.key
        return (UPLOAD_API if upload else API) + "/" + path + "?" + urllib.parse.urlencode(p)

    def get(self, path, params):
        return http("GET", self._u(path, params), headers=self._h())

    def send(self, method, path, params, body):
        return http(method, self._u(path, params), data=body, headers=self._h())

    def upload(self, path, params, meta, filedata, mime):
        boundary = "ytpush" + uuid.uuid4().hex
        parts = (
            "--%s\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n%s\r\n"
            "--%s\r\nContent-Type: %s\r\n\r\n" % (boundary, json.dumps(meta), boundary, mime)
        ).encode() + filedata + ("\r\n--%s--\r\n" % boundary).encode()
        p = dict(params)
        p["uploadType"] = "multipart"
        h = self._h()
        h["Content-Type"] = "multipart/related; boundary=" + boundary
        return http("POST", self._u(path, p, upload=True), headers=h, raw=parts)


# ------------------------------------------------------------------ saved sign-in
def _fernet(secret):
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return None
    k = hashlib.sha256(("yt-push|" + secret).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(k))


def load_saved_refresh(secret):
    f = _fernet(secret) if secret else None
    if not f or not os.path.exists(TOKEN_FILE):
        return ""
    try:
        return f.decrypt(open(TOKEN_FILE, "rb").read()).decode()
    except Exception:
        print("saved sign-in could not be opened (client secret changed?); a new sign-in is needed")
        return ""


def save_refresh(secret, rt):
    f = _fernet(secret)
    if not f:
        print("cryptography is not installed: sign-in not saved")
        return False
    with open(TOKEN_FILE, "wb") as fh:
        fh.write(f.encrypt(rt.encode()))
    git_publish([os.path.relpath(TOKEN_FILE, REPO)], "yt-push: save encrypted sign-in")
    return True


def refresh_access(cid, sec, rt):
    st, js = http("POST", "https://oauth2.googleapis.com/token", form=True, data={
        "client_id": cid, "client_secret": sec, "refresh_token": rt, "grant_type": "refresh_token"})
    if st == 200 and js.get("access_token"):
        return js["access_token"]
    print("saved sign-in rejected:", st, js.get("error", ""), js.get("error_description", ""))
    return None


def creds():
    return os.environ.get("YT_CLIENT_ID", "").strip(), os.environ.get("YT_CLIENT_SECRET", "").strip()


def get_token(allow_device=False):
    cid, sec = creds()
    if not cid or not sec:
        print(SETUP_TEXT)
        return None
    for rt in (os.environ.get("YT_REFRESH_TOKEN", "").strip(), load_saved_refresh(sec)):
        if rt:
            tok = refresh_access(cid, sec, rt)
            if tok:
                return tok
    if not allow_device:
        print("No working sign-in yet. Run the yt-push workflow once with mode signin.")
        return None
    return device_signin(cid, sec)


def device_signin(cid, sec):
    st, js = http("POST", "https://oauth2.googleapis.com/device/code", form=True,
                  data={"client_id": cid, "scope": SCOPE})
    if st != 200 or "device_code" not in js:
        print("device code request failed:", st, str(js)[:300])
        return None
    code, url = js["user_code"], js.get("verification_url", "https://www.google.com/device")
    wait_s, interval = int(js.get("expires_in", 1800)), int(js.get("interval", 5))
    os.makedirs(REPORTS, exist_ok=True)
    note = os.path.join(REPORTS, "SIGN-IN-CODE.txt")
    with open(note, "w") as f:
        f.write("OPEN %s AND TYPE: %s\nPick Blessed Prayers, tap Allow. Good for %d minutes from %s UTC.\n"
                % (url, code, wait_s // 60, time.strftime("%H:%M", time.gmtime())))
    print("SIGN-IN NEEDED: open %s and type %s (good for %d minutes)" % (url, code, wait_s // 60))
    git_publish([os.path.relpath(note, REPO)], "yt-push sign-in code")
    deadline = time.time() + wait_s
    while time.time() < deadline:
        time.sleep(interval)
        st, t = http("POST", "https://oauth2.googleapis.com/token", form=True, data={
            "client_id": cid, "client_secret": sec, "device_code": js["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"})
        if st == 200 and t.get("access_token"):
            try:
                os.remove(note)
                git_publish([os.path.relpath(note, REPO)], "yt-push sign-in code used")
            except OSError:
                pass
            if t.get("refresh_token"):
                save_refresh(sec, t["refresh_token"])
                print("signed in and saved: later runs need no tap")
            return t["access_token"]
        err = t.get("error", "")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 5
            continue
        print("sign-in stopped:", err or st)
        return None
    print("sign-in code expired before it was approved")
    return None


# ------------------------------------------------------------------ git
def git_publish(paths, msg):
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    subprocess.run(["git", "config", "user.name", "yt-push-bot"], cwd=REPO)
    subprocess.run(["git", "config", "user.email", "noreply@github.com"], cwd=REPO)
    subprocess.run(["git", "add", "-A", "--"] + paths, cwd=REPO)
    if subprocess.run(["git", "commit", "-q", "-m", msg], cwd=REPO).returncode != 0:
        return
    for _ in range(5):
        subprocess.run(["git", "fetch", "-q", "--depth=20", "origin", "main"], cwd=REPO)
        subprocess.run(["git", "rebase", "-q", "origin/main"], cwd=REPO)
        if subprocess.run(["git", "push", "-q"], cwd=REPO).returncode == 0:
            return
        time.sleep(3)


# ------------------------------------------------------------------ job building
def tag_chars(tags):
    return sum(len(t) + (2 if " " in t else 0) for t in tags) + max(0, len(tags) - 1)


def fit_tags(tags):
    out, seen = [], set()
    for t in tags:
        t = t.strip().replace("<", "").replace(">", "")
        if not t or t.lower() in seen:
            continue
        if tag_chars(out + [t]) > MAX_TAGS:
            break
        seen.add(t.lower())
        out.append(t)
    return out


def resolve_job(job):
    """Turn a job (with an optional IQ Vid pack) into the exact changes wanted. Returns (want, problems)."""
    want, problems = {}, []
    if job.get("pack"):
        path = os.path.join(REPO, job["pack"])
        try:
            pack = json.load(open(path, encoding="utf-8"))
            pick = (job.get("title_pick") or "A").upper()
            titles = pack.get("titles") or []
            t = next((x["text"] for x in titles if str(x.get("label", "")).upper().startswith(pick)), None)
            if t is None and titles:
                t = titles[0]["text"]
            if t:
                want["title"] = t
            desc = pack.get("description") or ""
            chaps = pack.get("chapters") or []
            if desc and chaps and "0:00" not in desc:
                block = "\n".join("%s %s" % (c["timestamp"], c["name"]) for c in chaps)
                desc = desc.rstrip() + "\n\n" + block
            if desc:
                want["description"] = desc
            if pack.get("tags"):
                want["tags"] = pack["tags"]
            fails = [v for v in pack.get("validation", []) if v.get("status") == "FAIL"]
            for v in fails:
                problems.append("IQ Vid FAIL left in pack: %s - %s" % (v.get("area"), v.get("check")))
        except Exception as e:
            problems.append("pack unreadable: %s" % e)
    for k in ("title", "description", "tags", "category_id", "default_language",
              "localized_titles", "playlist_ids", "comment", "captions_file", "captions_lang", "captions_name"):
        if job.get(k) not in (None, "", [], {}):
            want[k] = job[k]
    if "title" in want:
        want["title"] = want["title"].strip().replace("<", "").replace(">", "")
        if len(want["title"]) > MAX_TITLE:
            problems.append("title is %d characters (max %d)" % (len(want["title"]), MAX_TITLE))
    if "description" in want:
        want["description"] = want["description"].replace("<", "").replace(">", "")
        if len(want["description"].encode("utf-8")) > MAX_DESC:
            problems.append("description is over %d bytes" % MAX_DESC)
    if "tags" in want:
        fitted = fit_tags(want["tags"])
        if len(fitted) < len(want["tags"]):
            problems.append("tags trimmed from %d to %d to stay under %d characters"
                            % (len(want["tags"]), len(fitted), MAX_TAGS))
        want["tags"] = fitted
    if "captions_file" in want and not os.path.exists(os.path.join(REPO, want["captions_file"])):
        problems.append("captions file not found: %s" % want["captions_file"])
    return want, problems


def blocking(problems):
    return [p for p in problems if not p.startswith("tags trimmed")]


# ------------------------------------------------------------------ apply one job
def read_video(yt, vid):
    st, js = yt.get("videos", {"part": "snippet,localizations,status", "id": vid})
    if st != 200:
        return None, "videos.list %s %s" % (st, str(js)[:200])
    items = js.get("items", [])
    if not items:
        return None, "video not found (wrong id, deleted, or private and no sign-in)"
    return items[0], None


def plan_changes(live, want):
    sn = live.get("snippet", {})
    locs = live.get("localizations", {}) or {}
    diff, notes = {}, []
    if "title" in want and want["title"] != sn.get("title"):
        diff["title"] = (sn.get("title"), want["title"])
    if "description" in want and want["description"].strip() != (sn.get("description") or "").strip():
        diff["description"] = (len(sn.get("description") or ""), len(want["description"]))
    if "tags" in want and [t.lower() for t in want["tags"]] != [t.lower() for t in sn.get("tags", [])]:
        diff["tags"] = (len(sn.get("tags", [])), len(want["tags"]))
    if "category_id" in want and str(want["category_id"]) != str(sn.get("categoryId")):
        diff["categoryId"] = (sn.get("categoryId"), str(want["category_id"]))
    if "default_language" in want and want["default_language"] != sn.get("defaultLanguage"):
        diff["defaultLanguage"] = (sn.get("defaultLanguage"), want["default_language"])
    loc_changes = {}
    for lang, title in (want.get("localized_titles") or {}).items():
        keys = [k for k in locs if k == lang or k.split("-")[0].lower() == lang.lower()]
        if not keys:
            notes.append("%s: video has no %s localization, skipped (we never add a language)" % (lang, lang))
            continue
        if len(title) > MAX_TITLE:
            notes.append("%s: localized title too long, skipped" % lang)
            continue
        for k in keys:
            if locs[k].get("title") != title:
                loc_changes[k] = title
    if loc_changes:
        diff["localizations"] = loc_changes
    return diff, notes


def build_body(vid, live, want, diff):
    sn = live["snippet"]
    snippet = {
        "title": want.get("title", sn.get("title", "")),
        "description": want.get("description", sn.get("description", "")),
        "categoryId": str(want.get("category_id", sn.get("categoryId", "22"))),
    }
    tags = want.get("tags", sn.get("tags"))
    if tags is not None:
        snippet["tags"] = tags
    for k, wk in (("defaultLanguage", "default_language"), ("defaultAudioLanguage", None)):
        v = want.get(wk) if wk else None
        v = v or sn.get(k)
        if v:
            snippet[k] = v
    body = {"id": vid, "snippet": snippet}
    parts = ["snippet"]
    if "localizations" in diff:
        merged = json.loads(json.dumps(live.get("localizations", {})))
        for k, t in diff["localizations"].items():
            merged[k]["title"] = t
        body["localizations"] = merged
        parts.append("localizations")
    return body, ",".join(parts)


def save_rollback(vid, live):
    os.makedirs(ROLLBACK, exist_ok=True)
    stamp = dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(ROLLBACK, "%s-%s.json" % (vid, stamp))
    json.dump({"video_id": vid, "saved_utc": stamp, "snippet": live.get("snippet"),
               "localizations": live.get("localizations", {})},
              open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return os.path.relpath(path, REPO)


def in_playlist(yt, pl, vid):
    st, js = yt.get("playlistItems", {"part": "id", "playlistId": pl, "videoId": vid, "maxResults": 1})
    return st == 200 and bool(js.get("items"))


def has_caption(yt, vid, lang):
    st, js = yt.get("captions", {"part": "snippet", "videoId": vid})
    if st != 200:
        return False
    return any(c["snippet"].get("language", "").split("-")[0] == lang.split("-")[0]
               and c["snippet"].get("trackKind") != "asr" for c in js.get("items", []))


def run_job(yt, job, mode):
    vid = job["video_id"]
    res = {"video_id": vid, "mode": mode, "time_utc": dt.datetime.utcnow().isoformat(timespec="seconds"),
           "changed": [], "skipped": [], "errors": []}
    want, problems = resolve_job(job)
    res["skipped"] += [p for p in problems if p not in blocking(problems)]
    if blocking(problems):
        res["errors"] += blocking(problems)
        return res
    live, err = read_video(yt, vid)
    if err:
        res["errors"].append(err)
        return res
    res["live_title"] = live["snippet"].get("title")
    diff, notes = plan_changes(live, want)
    res["skipped"] += notes
    print("\n%s | %s" % (vid, live["snippet"].get("title", "")[:80]))
    for k, v in diff.items():
        print("  %s: %s" % (k, v if k != "localizations" else ", ".join(v)))
    for n in notes:
        print("  " + n)

    if mode in ("dry", "verify"):
        res["would_change"] = sorted(diff)
        if mode == "dry":
            for extra in ("playlist_ids", "comment", "captions_file"):
                if extra in want:
                    res["would_change"].append(extra)
        return res

    # metadata
    if diff:
        res["rollback"] = save_rollback(vid, live)
        body, parts = build_body(vid, live, want, diff)
        st, js = yt.send("PUT", "videos", {"part": parts}, body)
        if st != 200:
            res["errors"].append("videos.update %s %s" % (st, str(js)[:300]))
            return res
        again, err = read_video(yt, vid)
        if err:
            res["errors"].append("re-read failed: " + err)
        else:
            d2, _ = plan_changes(again, want)
            if d2:
                res["errors"].append("saved but YouTube still shows a difference in: " + ", ".join(d2))
            else:
                res["changed"] += sorted(diff)
                print("  APPLIED + verified:", ", ".join(sorted(diff)))
    else:
        res["skipped"].append("metadata already matches")

    # playlists
    for pl in want.get("playlist_ids", []):
        if in_playlist(yt, pl, vid):
            res["skipped"].append("already in playlist " + pl)
            continue
        st, js = yt.send("POST", "playlistItems", {"part": "snippet"},
                         {"snippet": {"playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}})
        (res["changed"] if st == 200 else res["errors"]).append(
            "playlist %s" % pl if st == 200 else "playlist %s: %s %s" % (pl, st, str(js)[:200]))

    # comment (the API cannot pin; Studio pin stays a manual click)
    if want.get("comment"):
        st, js = yt.get("commentThreads", {"part": "snippet", "videoId": vid, "searchTerms": want["comment"][:40],
                                           "maxResults": 20})
        dup = st == 200 and any(
            it["snippet"]["topLevelComment"]["snippet"].get("authorChannelId", {}).get("value") == CHANNEL_ID
            and it["snippet"]["topLevelComment"]["snippet"].get("textOriginal", "").strip() == want["comment"].strip()
            for it in js.get("items", []))
        if dup:
            res["skipped"].append("comment already posted")
        else:
            st, js = yt.send("POST", "commentThreads", {"part": "snippet"},
                             {"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": want["comment"]}}}})
            (res["changed"] if st == 200 else res["errors"]).append(
                "comment posted (pin it in Studio)" if st == 200 else "comment: %s %s" % (st, str(js)[:200]))

    # captions
    if want.get("captions_file"):
        lang = want.get("captions_lang", "en")
        if has_caption(yt, vid, lang):
            res["skipped"].append("a %s caption track is already on the video" % lang)
        else:
            data = open(os.path.join(REPO, want["captions_file"]), "rb").read()
            st, js = yt.upload("captions", {"part": "snippet"},
                               {"snippet": {"videoId": vid, "language": lang,
                                            "name": want.get("captions_name", "English"), "isDraft": False}},
                               data, "application/octet-stream")
            (res["changed"] if st == 200 else res["errors"]).append(
                "captions %s" % lang if st == 200 else "captions: %s %s" % (st, str(js)[:200]))
    return res


# ------------------------------------------------------------------ modes
def queued_jobs():
    files = sorted(glob.glob(os.path.join(QUEUE, "*.json")))
    jobs = []
    for f in files:
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print("unreadable job %s: %s" % (os.path.basename(f), e))
            continue
        for j in (data if isinstance(data, list) else [data]):
            if isinstance(j, dict) and j.get("video_id"):
                jobs.append((f, j))
            else:
                print("job in %s has no video_id, skipped" % os.path.basename(f))
    return jobs


def finish_file(path, results, ok):
    os.makedirs(DONE, exist_ok=True)
    data = json.load(open(path, encoding="utf-8"))
    out = {"job": data, "results": results}
    stamp = dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    name = os.path.basename(path)[:-5] + "-" + stamp + (".json" if ok else ".FAILED.json")
    json.dump(out, open(os.path.join(DONE, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if ok:
        os.remove(path)
    else:
        # keep the job queued so a fix + push retries it; the failure note sits in done/
        pass


def mode_check():
    cid, sec = creds()
    print("YOUTUBE_API_KEY:", bool(os.environ.get("YOUTUBE_API_KEY")))
    print("YT_CLIENT_ID:", bool(cid), " YT_CLIENT_SECRET:", bool(sec))
    print("YT_REFRESH_TOKEN secret:", bool(os.environ.get("YT_REFRESH_TOKEN")),
          " saved sign-in file:", os.path.exists(TOKEN_FILE))
    if not (cid and sec):
        print(SETUP_TEXT)
        return 2
    tok = get_token(allow_device=False)
    if not tok:
        return 2
    st, js = YT(token=tok).get("channels", {"part": "snippet", "mine": "true"})
    names = [c["snippet"]["title"] for c in js.get("items", [])] if st == 200 else []
    print("signed in as channel:", names or (st, str(js)[:200]))
    if st == 200 and not any(c["id"] == CHANNEL_ID for c in js.get("items", [])):
        print("WARNING: the saved sign-in is NOT the Blessed Prayers channel. Run signin again and pick Blessed Prayers.")
        return 2
    return 0


def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else "dry").lower()
    if mode not in ("check", "dry", "apply", "verify", "signin"):
        print("mode must be check, dry, apply, verify or signin")
        return 2
    if mode == "check":
        return mode_check()
    if mode == "signin":
        return 0 if get_token(allow_device=True) else 2

    if mode == "verify":
        cutoff = time.time() - 7 * 86400
        files = [f for f in glob.glob(os.path.join(DONE, "*.json"))
                 if os.path.getmtime(f) >= cutoff and not f.endswith(".FAILED.json")]
        jobs = []
        for f in files:
            d = json.load(open(f, encoding="utf-8"))["job"]
            jobs += [(f, j) for j in (d if isinstance(d, list) else [d])]
    else:
        jobs = queued_jobs()
    if not jobs:
        print("Nothing queued. No API calls made.")
        return 0

    tok = get_token(allow_device=False)
    if mode == "apply" and not tok:
        return 2
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not tok and not key:
        print("Neither a sign-in nor YOUTUBE_API_KEY is available.")
        return 2
    yt = YT(key=key, token=tok)
    if not tok:
        print("(reading with the API key only: private and scheduled videos will show as not found)")

    by_file, failures = {}, 0
    for path, job in jobs:
        r = run_job(yt, job, mode)
        if mode == "verify":
            r["verify"] = "OK" if not r.get("would_change") and not r["errors"] else "DIFFERENT"
            print("  verify:", r["verify"], r.get("would_change", ""))
        by_file.setdefault(path, []).append(r)
        if r["errors"]:
            failures += 1
            for e in r["errors"]:
                print("  ERROR:", e)
        time.sleep(0.5)

    os.makedirs(REPORTS, exist_ok=True)
    summary = os.path.join(REPORTS, "last-%s.json" % mode)
    json.dump(by_file and {os.path.basename(k): v for k, v in by_file.items()},
              open(summary, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if mode == "apply":
        for path, results in by_file.items():
            finish_file(path, results, ok=not any(r["errors"] for r in results))
        git_publish([os.path.relpath(QUEUE, REPO), os.path.relpath(REPORTS, REPO)], "yt-push applied")
    print("\nSUMMARY mode=%s jobs=%d failed=%d" % (mode, len(jobs), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
