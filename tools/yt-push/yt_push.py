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
    "captions_name": "English",
    "thumbnail_file": "tools/yt-push/thumbs/x.jpg"     JPG/PNG, 2 MB max, 1280x720 best
  }

MODES
  check   which secrets exist and whether a saved sign-in works. No writes.
  dry     shows exactly what each queued job would change. Read-only.
  apply   writes every queued job. Default when the workflow fires on a push.
  verify  re-reads the videos in queue/done/ from the last 7 days and compares.
  signin  one-time Google sign-in by device code; the sign-in is saved encrypted so later runs
          need no tap.
  recent  lists the channel's uploads from the last 3 days (public, private AND scheduled, with
          publish time, Short or long, category, language, tag count, playlists) plus every channel
          playlist id+title, into reports/yt-push/recent.json. No writes. The nightly Studio finish
          starts here instead of the browser (YT-PUSH FIRST rule, Neko Nov 16 2026).
  A job may also carry "playlist_names": ["exact playlist title"]; they are resolved to ids.

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
CHANNEL_NAME = "Blessed Prayers"
# PROFILE picks which channel this run works on (Neko Nov 21 2026: Skip comedy goes to Big Skip).
# Each channel has its own saved sign-in file; same Google client, same quota.
PROFILE = os.environ.get("YTP_PROFILE", "bp").strip().lower() or "bp"
if PROFILE == "bigskip":
    CHANNEL_ID = "UCw_zfZtPSIg_LjQURb3o6MQ"
    CHANNEL_NAME = "Big Skip"
    TOKEN_FILE = os.path.join(HERE, "signin-bigskip.enc")
    QUEUE = os.path.join(HERE, "queue-bigskip")
    DONE = os.path.join(QUEUE, "done")
UPLOADS = os.path.join(HERE, "uploads", PROFILE)
UPLOADS_DONE = os.path.join(UPLOADS, "done")
MAX_UPLOADS_PER_RUN = int(os.environ.get("YTP_MAX_UPLOADS", "5"))  # insert = 1,600 quota units
# Device sign-in only allows "youtube" (not force-ssl). It covers videos.update, playlistItems
# and captions; posting comments needs force-ssl, so a comment that is refused is skipped, not failed.
SCOPE = "https://www.googleapis.com/auth/youtube"
# Full read+write (captions, comments) needs force-ssl too. signin asks for it first and falls back
# to plain "youtube" only if Google refuses the scope for this client type.
FULL_SCOPE = SCOPE + " https://www.googleapis.com/auth/youtube.force-ssl"
MAX_TITLE, MAX_DESC, MAX_TAGS = 100, 5000, 500

SETUP_TEXT = """\
ONE-TIME SETUP (Google credentials are Neko-only, his rule):
  1. As blessedprayers4: console.cloud.google.com/auth/clients?project=curious-song-514322-u2
     (project "BP Uploader": consent screen already In production).
  2. Create client > "TV and Limited Input devices" > name yt-push > Create. Copy Client ID and secret.
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

    def upload_media(self, path, params, filedata, mime):
        p = dict(params)
        p["uploadType"] = "media"
        h = self._h()
        h["Content-Type"] = mime
        return http("POST", self._u(path, p, upload=True), headers=h, raw=filedata)


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
                  data={"client_id": cid, "scope": FULL_SCOPE})
    if st != 200 or "device_code" not in js:
        print("full read+write scope refused:", st, str(js)[:300], "-> retrying with plain youtube scope")
        st, js = http("POST", "https://oauth2.googleapis.com/device/code", form=True,
                      data={"client_id": cid, "scope": SCOPE})
    else:
        print("device code issued WITH full read+write scope (youtube + youtube.force-ssl)")
    if st != 200 or "device_code" not in js:
        print("device code request failed:", st, str(js)[:300])
        return None
    code, url = js["user_code"], js.get("verification_url", "https://www.google.com/device")
    wait_s, interval = int(js.get("expires_in", 1800)), int(js.get("interval", 5))
    os.makedirs(REPORTS, exist_ok=True)
    note = os.path.join(REPORTS, "SIGN-IN-CODE%s.txt" % ("" if PROFILE == "bp" else "-" + PROFILE))
    with open(note, "w") as f:
        f.write("OPEN %s AND TYPE: %s\nPick %s, tap Allow. Good for %d minutes from %s UTC.\n"
                % (url, code, CHANNEL_NAME, wait_s // 60, time.strftime("%H:%M", time.gmtime())))
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
              "localized_titles", "playlist_ids", "playlist_names", "comment", "captions_file", "captions_lang", "captions_name", "thumbnail_file"):
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
    if "thumbnail_file" in want:
        tp = os.path.join(REPO, want["thumbnail_file"])
        if not os.path.exists(tp):
            problems.append("thumbnail not found: %s" % want["thumbnail_file"])
        elif os.path.getsize(tp) > 2 * 1024 * 1024:
            problems.append("thumbnail is over 2 MB (YouTube's limit)")
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


def _tagset(tags):
    # YouTube may reorder tags and normalise spacing/quotes, so compare as a set
    return {" ".join(str(t).replace("\u2019", "'").lower().split()) for t in tags}


def plan_changes(live, want):
    sn = live.get("snippet", {})
    locs = live.get("localizations", {}) or {}
    diff, notes = {}, []
    if "title" in want and want["title"] != sn.get("title"):
        diff["title"] = (sn.get("title"), want["title"])
    if "description" in want and want["description"].strip() != (sn.get("description") or "").strip():
        diff["description"] = (len(sn.get("description") or ""), len(want["description"]))
    if "tags" in want and _tagset(want["tags"]) != _tagset(sn.get("tags", [])):
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
    stamp = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).strftime("%Y%m%d-%H%M%S")
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
    res = {"video_id": vid, "mode": mode, "time_utc": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds"),
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
            for extra in ("playlist_ids", "comment", "captions_file", "thumbnail_file"):
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
        again, err, d2 = None, None, None
        for wait in (0, 8, 20, 40):  # YouTube's read-back lags a few seconds behind a save
            time.sleep(wait)
            again, err = read_video(yt, vid)
            if err:
                continue
            d2, _ = plan_changes(again, want)
            if not d2:
                break
        if err:
            res["errors"].append("re-read failed: " + err)
        else:
            if d2:
                res["errors"].append("saved but YouTube still shows a difference in: " + ", ".join(d2))
            else:
                res["changed"] += sorted(diff)
                print("  APPLIED + verified:", ", ".join(sorted(diff)))
    else:
        res["skipped"].append("metadata already matches")

    # playlists
    names = want.get("playlist_names") or job.get("playlist_names") or []
    if names and mode == "apply":
        found = my_playlists(yt)
        for n in names:
            if n.strip() in found:
                want.setdefault("playlist_ids", []).append(found[n.strip()])
            else:
                res["errors"].append("playlist not found by name: " + n)
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
            if st == 200:
                res["changed"].append("comment posted (pin it in Studio)")
            elif st == 403:
                res["skipped"].append("comment not allowed with this sign-in (YouTube needs a wider one): post + pin in Studio")
            else:
                res["errors"].append("comment: %s %s" % (st, str(js)[:200]))

    # thumbnail (re-sent every apply only when the file differs from the last one we set)
    if want.get("thumbnail_file"):
        data = open(os.path.join(REPO, want["thumbnail_file"]), "rb").read()
        mime = "image/png" if want["thumbnail_file"].lower().endswith(".png") else "image/jpeg"
        st, js = yt.upload_media("thumbnails/set", {"videoId": vid}, data, mime)
        if st == 200:
            res["changed"].append("thumbnail")
        elif st == 403:
            res["errors"].append("thumbnail refused (403): the channel needs custom thumbnails turned on "
                                 "(Studio > Settings > Channel > Feature eligibility, phone verification)")
        else:
            res["errors"].append("thumbnail: %s %s" % (st, str(js)[:200]))

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
    stamp = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).strftime("%Y%m%d-%H%M%S")
    name = os.path.basename(path)[:-5] + "-" + stamp + (".json" if ok else ".FAILED.json")
    json.dump(out, open(os.path.join(DONE, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if ok:
        os.remove(path)
    else:
        # keep the job queued so a fix + push retries it; the failure note sits in done/
        pass


def my_playlists(yt):
    out, page = {}, None
    while True:
        p = {"part": "snippet", "mine": "true", "maxResults": 50}
        if page:
            p["pageToken"] = page
        st, js = yt.get("playlists", p)
        if st != 200:
            break
        for it in js.get("items", []):
            out[it["snippet"]["title"].strip()] = it["id"]
        page = js.get("nextPageToken")
        if not page:
            break
    return out


def _secs(iso):
    import re
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, se = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + se


def mode_recent():
    tok = get_token(allow_device=False)
    if not tok:
        return 2
    yt = YT(token=tok)
    st, js = yt.get("channels", {"part": "contentDetails", "id": CHANNEL_ID})
    if st != 200 or not js.get("items"):
        print("channel read failed", st, str(js)[:200])
        return 1
    uploads = js["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    st, js = yt.get("playlistItems", {"part": "contentDetails", "playlistId": uploads, "maxResults": 40})
    ids = [i["contentDetails"]["videoId"] for i in js.get("items", [])] if st == 200 else []
    pls = my_playlists(yt)
    cutoff = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(days=3)
    vids = []
    if ids:
        st, js = yt.get("videos", {"part": "snippet,status,contentDetails", "id": ",".join(ids)})
        for v in js.get("items", []) if st == 200 else []:
            sn, stt = v["snippet"], v["status"]
            when = stt.get("publishAt") or sn.get("publishedAt")
            try:
                w = dt.datetime.strptime(when[:19], "%Y-%m-%dT%H:%M:%S")
            except Exception:
                w = cutoff
            if w < cutoff and not stt.get("publishAt"):
                continue
            secs = _secs(v["contentDetails"].get("duration"))
            vids.append({"id": v["id"], "title": sn.get("title"), "published_utc": sn.get("publishedAt"),
                         "publish_at_utc": stt.get("publishAt"), "privacy": stt.get("privacyStatus"),
                         "kind": "short" if secs and secs <= 180 else "long", "seconds": secs,
                         "categoryId": sn.get("categoryId"), "language": sn.get("defaultLanguage") or sn.get("defaultAudioLanguage"),
                         "tag_count": len(sn.get("tags", []))})
    out = {"made_utc": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat() + "Z", "videos": vids, "playlists": pls}
    os.makedirs(REPORTS, exist_ok=True)
    path = os.path.join(REPORTS, "recent.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for v in vids:
        print(v["id"], v["kind"], v["privacy"], v["publish_at_utc"] or v["published_utc"], "cat", v["categoryId"],
              "lang", v["language"], "tags", v["tag_count"], "|", v["title"])
    print("playlists:", len(pls))
    git_publish([os.path.relpath(REPORTS, REPO)], "yt-push recent list")
    return 0


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
        print("WARNING: the saved sign-in is NOT the %s channel. Run signin again and pick %s." % (CHANNEL_NAME, CHANNEL_NAME))
        return 2
    return 0


# ------------------------------------------------------------------ upload (new videos)
def _utc(s):
    return dt.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")


def channel_videos(yt):
    """title -> {id, privacy, publishAt} for every upload on the channel (private and scheduled too)."""
    st, js = yt.get("channels", {"part": "contentDetails", "id": CHANNEL_ID})
    if st != 200 or not js.get("items"):
        return {}
    pl = js["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, page = [], None
    for _ in range(10):
        p = {"part": "contentDetails", "playlistId": pl, "maxResults": 50}
        if page:
            p["pageToken"] = page
        st, js = yt.get("playlistItems", p)
        if st != 200:
            break
        ids += [i["contentDetails"]["videoId"] for i in js.get("items", [])]
        page = js.get("nextPageToken")
        if not page:
            break
    out = {}
    for i in range(0, len(ids), 50):
        st, js = yt.get("videos", {"part": "snippet,status", "id": ",".join(ids[i:i + 50])})
        for v in js.get("items", []) if st == 200 else []:
            out[v["snippet"]["title"].strip().lower()] = {"id": v["id"], "privacy": v["status"].get("privacyStatus"),
                                                         "publishAt": v["status"].get("publishAt"),
                                                         "snippet": v["snippet"]}
    return out


def _status(job, when):
    st = {"selfDeclaredMadeForKids": bool(job.get("made_for_kids", False)),
          "containsSyntheticMedia": bool(job.get("synthetic", True)), "embeddable": True}
    if when:
        st["privacyStatus"] = "private"
        st["publishAt"] = when
    else:
        st["privacyStatus"] = job.get("privacy", "public")
    return st


def _publish_time(job):
    """The job's publish time, moved 20 minutes ahead if it has already passed (YouTube refuses past times)."""
    w = job.get("publish_at_utc", "")
    if not w:
        return ""
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    t = _utc(w)
    if t < now + dt.timedelta(minutes=10):
        t = now + dt.timedelta(minutes=20)
    return t.strftime("%Y-%m-%dT%H:%M:00Z")


SLOT_HOURS_UTC = (17, 23)  # 12 PM and 6 PM ET (EST); the channel's two daily posting slots


def _next_slot(after):
    d = after.replace(minute=0, second=0, microsecond=0)
    for _ in range(24 * 60):
        for h in SLOT_HOURS_UTC:
            c = d.replace(hour=h)
            if c >= after:
                return c
        d = (d + dt.timedelta(days=1)).replace(hour=0)
    return after


def reslot(jobs):
    """Keeps the queue in order with no bunching: a job whose time has passed (sign-in came late, a day
    was missed) moves to the next free 12 PM / 6 PM slot after the job before it, and every later job
    moves along behind it. Times still in the future and in order are left alone."""
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    taken = set()  # never land on top of what's already scheduled
    for f in glob.glob(os.path.join(UPLOADS_DONE, "*.json")):
        w = json.load(open(f, encoding="utf-8")).get("publish_at_utc")
        if w:
            taken.add(_utc(w))
    last = None
    for path, _, job in [(j[1], 0, j[2]) for j in jobs]:
        own = _utc(job["publish_at_utc"]) if job.get("publish_at_utc") else None
        floor = now + dt.timedelta(minutes=30)
        if last:
            floor = max(floor, last + dt.timedelta(minutes=1))
        t = own if own and own >= floor and own not in taken else None
        while t is None or t in taken:
            t = _next_slot(floor if t is None else t + dt.timedelta(minutes=1))
        if own != t:
            print("moved", job.get("title", "")[:50], own, "->", t)
            job["publish_at_utc"] = t.strftime("%Y-%m-%dT%H:%M:00Z")
            json.dump(job, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        taken.add(t)
        last = t


def upload_one(yt, job):
    snippet = {"title": job["title"][:MAX_TITLE], "description": job.get("description", "")[:MAX_DESC],
               "tags": fit_tags(job.get("tags", [])), "categoryId": str(job.get("category_id", "23")),
               "defaultLanguage": job.get("language", "en"), "defaultAudioLanguage": job.get("language", "en")}
    when = _publish_time(job)
    meta = {"snippet": snippet, "status": _status(job, when)}
    src = job["video_url"]
    req = urllib.request.Request(src, headers={"User-Agent": "yt-push"})
    data = urllib.request.urlopen(req, timeout=300).read()
    if len(data) < 100000:
        return None, "video download too small (%d bytes) from %s" % (len(data), src)
    h = {"Authorization": "Bearer " + yt.token, "Content-Type": "application/json; charset=UTF-8",
         "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(data))}
    url = UPLOAD_API + "/videos?" + urllib.parse.urlencode({"uploadType": "resumable", "part": "snippet,status"})
    r = urllib.request.Request(url, data=json.dumps(meta).encode(), method="POST", headers=h)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            loc = resp.headers.get("Location")
    except urllib.error.HTTPError as e:
        return None, "upload start refused %s %s" % (e.code, e.read().decode("utf-8", "replace")[:400])
    r = urllib.request.Request(loc, data=data, method="PUT", headers={"Content-Type": "video/mp4"})
    try:
        with urllib.request.urlopen(r, timeout=1800) as resp:
            js = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return None, "upload refused %s %s" % (e.code, e.read().decode("utf-8", "replace")[:400])
    return js.get("id"), when


def gate_block(job):
    """Big Skip only. Returns why the job may not upload, or '' when its gate record passes.
    Record: tools/yt-push/gate/<video file name>.json = {"voice_gate": "PASS", "qa": "PASS",
    "qa_report": "<repo path>", "neko_ok": "<date + his words>"}. Written by tools/skip-voice/gate.py;
    neko_ok is filled in only after Neko has watched that exact file."""
    if PROFILE != "bigskip":
        return ""
    name = os.path.basename(job.get("video_url", ""))
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate", name + ".json")
    if not os.path.exists(p):
        return "no gate record (tools/yt-push/gate/%s.json)" % name
    try:
        g = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        return "gate record unreadable: %s" % e
    for k in ("voice_gate", "qa"):
        if g.get(k) != "PASS":
            return "%s is %r, not PASS" % (k, g.get(k))
    if not str(g.get("neko_ok") or "").strip():
        return "Neko has not OK'd this file"
    return ""


def mode_upload():
    """Uploads queued new videos (tools/yt-push/uploads/<profile>/*.json, one video per file), earliest
    publish time first, at most MAX_UPLOADS_PER_RUN a run (YouTube quota). A video whose exact title is
    already on the channel is not uploaded twice: if it sits there private and unscheduled, it just gets
    the job's publish time. Each finished job moves to uploads/<profile>/done/ with the video id."""
    files = sorted(glob.glob(os.path.join(UPLOADS, "*.json")))
    if not files:
        print("Nothing to upload.")
        return 0
    tok = get_token(allow_device=False)
    if not tok:
        return 2
    yt = YT(token=tok)
    st, js = yt.get("channels", {"part": "snippet", "mine": "true"})
    if st != 200 or not any(c["id"] == CHANNEL_ID for c in js.get("items", [])):
        print("STOP: the saved sign-in is not %s (%s). Nothing uploaded." % (CHANNEL_NAME, st))
        return 2
    jobs = []
    for f in files:
        j = json.load(open(f, encoding="utf-8"))
        jobs.append((j.get("publish_at_utc") or "9999", f, j))
    jobs.sort()
    reslot(jobs)
    have = channel_videos(yt)
    os.makedirs(UPLOADS_DONE, exist_ok=True)
    done_n, failures, uploaded = [], 0, 0
    for _, f, job in jobs:
        key = job["title"][:MAX_TITLE].strip().lower()
        res = {"time_utc": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")}
        if key in have:
            v = have[key]
            res["video_id"] = v["id"]
            if v["privacy"] == "private" and not v["publishAt"] and job.get("publish_at_utc"):
                when = _publish_time(job)
                body = {"id": v["id"], "status": _status(job, when)}
                st2, js2 = yt.send("PUT", "videos", {"part": "status"}, body)
                res["result"] = "already on channel; scheduled %s (%s)" % (when, st2)
                if st2 != 200:
                    res["error"] = str(js2)[:300]
            else:
                res["result"] = "already on channel (%s %s); not uploaded again" % (v["privacy"], v["publishAt"] or "")
        else:
            why = gate_block(job)
            if why:
                # SKIP GATE (Neko Nov 26 2026): no Big Skip video uploads without a passed gate record.
                print("[SKIP GATE] held %s: %s" % (os.path.basename(f), why))
                failures += 1
                continue
            if uploaded >= MAX_UPLOADS_PER_RUN:
                continue
            vid, info = upload_one(yt, job)
            uploaded += 1
            if vid:
                res["video_id"], res["result"] = vid, "uploaded; goes public %s" % (info or "now")
            else:
                res["error"] = info
                if "quota" in (info or "").lower():
                    print("quota used up for today; the rest waits for the next run")
                    print(os.path.basename(f), "ERROR", info)
                    failures += 1
                    break
        print(os.path.basename(f), "->", res.get("video_id", ""), res.get("result", ""), res.get("error", ""))
        if res.get("error"):
            failures += 1
            continue
        job["result"] = res
        dest = os.path.join(UPLOADS_DONE, os.path.basename(f))
        json.dump(job, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        os.remove(f)
        done_n.append(dest)
        time.sleep(1)
    left = len(glob.glob(os.path.join(UPLOADS, "*.json")))
    print("\nSUMMARY upload profile=%s done=%d failed=%d still queued=%d" % (PROFILE, len(done_n), failures, left))
    git_publish([os.path.relpath(UPLOADS, REPO)], "yt-push upload %s: %d done" % (PROFILE, len(done_n)))
    return 1 if failures else 0


def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else "dry").lower()
    if mode not in ("check", "dry", "apply", "verify", "signin", "recent", "upload"):
        print("mode must be check, dry, apply, verify, signin, recent or upload")
        return 2
    print("profile:", PROFILE, "channel:", CHANNEL_NAME, CHANNEL_ID)
    if mode == "upload":
        return mode_upload()
    if mode == "recent":
        return mode_recent()
    if mode == "check":
        return mode_check()
    if mode == "signin":
        # signin always asks fresh, so a new tap can widen the scope (Neko Nov 21: read and write)
        cid, sec = os.environ.get("YT_CLIENT_ID", "").strip(), os.environ.get("YT_CLIENT_SECRET", "").strip()
        tok = device_signin(cid, sec) if (cid and sec) else get_token(allow_device=True)
        if not tok:
            return 2
        rc = mode_check()
        if rc == 0 and glob.glob(os.path.join(UPLOADS, "*.json")):
            print("\nsigned in: uploading the queue now")
            return mode_upload()
        return rc

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
