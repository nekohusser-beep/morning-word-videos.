#!/usr/bin/env python3
"""desk-poster / yt_studio_upload.py - uploads + schedules Blessed Prayers videos from the laptop, as you.

WHY: Google locks any video uploaded through our own API project to private (unverified-app rule), so
uploads have gone through the Studio pane: the MP4 pushed to GitHub in 16 MB chunks, a JavaScript driver
stitching them back inside the browser, sign-outs killing runs. The GitHub tools that solve this
(wanghaisheng/youtube-auto-upload "ytb-up", dreammis/social-auto-upload) all do the same thing: drive the
real upload page in a real browser with a saved sign-in, at human speed. That is what this is, rebuilt
for us with the Studio selectors our own driver already proved (workflows/long-reading-parts/
studio-upload-driver.js, Nov 11 schedule steps in LESSONS). The file goes straight from the laptop disk:
no chunks, no GitHub hop. Because it is YOUR browser session, the video posts public/scheduled normally.

JOB: a .json next to the .mp4 in Desktop\\Claude-Work\\desk-poster\\queue\\ (same name):
  {"title": "...", "description": "...", "tags": ["..."], "thumbnail": "x.jpg",       (IQ Vid output)
   "playlist": "Exact Playlist Title",
   "when": "now" | {"date": "Nov 16, 2026", "time": "5:00 AM"},
   "altered_content": true}                                                         (AI-made = true)
A job with no title, description or tags is refused (IQ Vid gate). Results: queue\\done\\<name>.result.json

FIRST RUN: a Chrome window opens on its own profile; sign in to the Blessed Prayers Google account once.
It stays signed in (profile saved in desk-poster\\profile). After that: double-click Run-Uploader.cmd.
"""
import json
import os
import shutil
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

CHANNEL = "UCaKI8Xsi-MHu78UnJTY1xpg"
HOME = Path(os.environ.get("DESK_POSTER_HOME", Path.home() / "Desktop" / "Claude-Work" / "desk-poster"))
QUEUE, DONE, PROFILE = HOME / "queue", HOME / "queue" / "done", HOME / "profile"
UPLOAD_URL = "https://studio.youtube.com/channel/%s/videos/upload?d=ud" % CHANNEL


def log(*a):
    line = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(HOME / "uploader.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def gate(job):
    missing = [k for k in ("title", "description", "tags") if not job.get(k)]
    if missing:
        return "IQ VID GATE: job has no " + ", ".join(missing)
    if len(job["title"]) > 100:
        return "title over 100 characters"
    return None


def visible(page, selector):
    return page.locator(selector).filter(has_not=page.locator("[hidden]")).first


def upload_one(page, mp4: Path, job: dict) -> dict:
    res = {"file": mp4.name, "steps": []}
    step = lambda s: (res["steps"].append(s), log("  ", s))
    page.goto(UPLOAD_URL, wait_until="domcontentloaded")
    if "accounts.google.com" in page.url:
        raise RuntimeError("not signed in: sign in to the Blessed Prayers account in this window, then rerun")
    dlg = page.locator("ytcp-uploads-dialog")
    dlg.locator("input[type=file]").first.wait_for(state="attached", timeout=60000)
    dlg.locator("input[type=file]").first.set_input_files(str(mp4))
    step("file sent")

    boxes = dlg.locator("#textbox")
    boxes.nth(1).wait_for(timeout=180000)
    for idx, val in ((0, job["title"]), (1, job["description"])):
        b = boxes.nth(idx)
        b.click()
        page.keyboard.press("Control+A")
        page.keyboard.insert_text(val)
        time.sleep(0.6)
    step("title + description")

    if job.get("thumbnail"):
        thumb = mp4.parent / job["thumbnail"]
        if thumb.exists():
            dlg.locator("ytcp-thumbnail-uploader input#file-loader").set_input_files(str(thumb))
            time.sleep(1.5)
            step("thumbnail")

    if job.get("playlist"):
        dlg.locator("ytcp-video-metadata-playlists ytcp-dropdown-trigger").click()
        time.sleep(1.5)
        row = page.locator("ytcp-checkbox-group li").filter(has_text=job["playlist"]).first
        row.locator("#checkbox").click()
        time.sleep(0.7)
        page.locator("ytcp-button").filter(has_text="Done").last.click()
        time.sleep(0.9)
        if job["playlist"][:30] not in dlg.locator("ytcp-video-metadata-playlists ytcp-dropdown-trigger").inner_text():
            raise RuntimeError("playlist not set")
        step("playlist")

    dlg.locator("[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]").click()
    dlg.locator("ytcp-button").filter(has_text="Show more").first.click()
    time.sleep(1.2)
    alt = "VIDEO_HAS_ALTERED_CONTENT_YES" if job.get("altered_content", True) else "VIDEO_HAS_ALTERED_CONTENT_NO"
    dlg.locator("[name=%s]" % alt).click()
    tag_in = dlg.locator("ytcp-free-text-chip-bar input")
    tag_in.scroll_into_view_if_needed()
    tag_in.click()
    page.keyboard.insert_text(", ".join(job["tags"]))
    page.keyboard.press("Enter")
    time.sleep(0.9)
    chips = dlg.locator("ytcp-free-text-chip-bar ytcp-chip").count()
    step("not for kids, altered=%s, %d tags" % (alt.endswith("YES"), chips))

    for _ in range(3):
        dlg.locator("#next-button").click()
        time.sleep(1.5)

    when = job.get("when", "now")
    if when == "now":
        dlg.locator("tp-yt-paper-radio-button[name=PUBLIC]").click()
        step("visibility public")
    else:
        dlg.locator("#second-container-expand-button").click()
        time.sleep(1)
        if when.get("date"):
            dlg.locator("ytcp-datetime-picker #datepicker-trigger, ytcp-datetime-picker ytcp-dropdown-trigger").first.click()
            time.sleep(0.8)
            date_in = page.locator("tp-yt-paper-dialog input").filter(has_not=page.locator("[hidden]")).first
            date_in.click(click_count=3)
            page.keyboard.insert_text(when["date"])
            page.keyboard.press("Enter")
            time.sleep(0.8)
        time_in = dlg.locator("ytcp-datetime-picker #time-of-day-container input, ytcp-datetime-picker input").last
        time_in.click(click_count=3)
        page.keyboard.insert_text(when["time"])
        page.keyboard.press("Enter")
        time.sleep(0.8)
        shown = dlg.locator("ytcp-datetime-picker").inner_text().replace("\n", " ")
        step("schedule set: " + shown)
        if when["time"].split()[0] not in shown:
            raise RuntimeError("schedule time did not take: " + shown)

    prog = dlg.locator("ytcp-video-upload-progress")
    for _ in range(400):
        txt = prog.inner_text().replace("\n", " ")
        if "Checks complete" in txt:
            break
        if any(w in txt for w in ("Copyright", "copyright", "restriction", "Appeal")) and "No issues" not in txt:
            raise RuntimeError("YouTube check flagged: " + txt)
        time.sleep(5)
    else:
        raise RuntimeError("checks did not finish in time")
    step("checks: " + txt[:80])

    dlg.locator("#done-button").click()
    for _ in range(40):
        time.sleep(1.5)
        links = [a for a in page.locator("a[href*='youtu.be/']").evaluate_all("els => els.map(e => e.href)")]
        if links:
            res["video_id"] = links[0].split("youtu.be/")[1].split("?")[0]
            step("done: https://youtu.be/" + res["video_id"])
            return res
    raise RuntimeError("published but no link came back; check Studio")


REPO_API = "https://api.github.com/repos/nekohusser-beep/morning-word-videos./releases/tags/desk-queue"


def pull_remote():
    """Claude drops jobs (name.mp4 + name.json + thumbnail) as assets on the public release 'desk-queue'.
    The laptop pulls any it has not taken yet, so no laptop-linked chat is needed to load the queue."""
    import urllib.request
    taken_f = HOME / "pulled.txt"
    taken = set(taken_f.read_text().split()) if taken_f.exists() else set()
    try:
        with urllib.request.urlopen(urllib.request.Request(REPO_API, headers={"User-Agent": "desk-poster"}), timeout=60) as r:
            assets = json.loads(r.read()).get("assets", [])
    except Exception as e:
        log("pull skipped:", e)
        return
    for a in assets:
        key = "%s:%s" % (a["name"], a["id"])
        if key in taken:
            continue
        dest = QUEUE / a["name"]
        urllib.request.urlretrieve(a["browser_download_url"], str(dest))
        taken.add(key)
        log("pulled", a["name"])
    taken_f.write_text("\n".join(sorted(taken)))


def main():
    for d in (QUEUE, DONE, PROFILE):
        d.mkdir(parents=True, exist_ok=True)
    if "--login" not in sys.argv:
        pull_remote()
    jobs = sorted(p for p in QUEUE.glob("*.mp4") if p.with_suffix(".json").exists())
    login_only = "--login" in sys.argv
    if not jobs and not login_only:
        log("nothing in", QUEUE)
        return 0
    with sync_playwright() as pw:
        kw = dict(user_data_dir=str(PROFILE), headless=False, viewport={"width": 1366, "height": 860},
                  args=["--disable-blink-features=AutomationControlled"])
        try:
            ctx = pw.chromium.launch_persistent_context(channel="chrome", **kw)
        except Exception:
            ctx = pw.chromium.launch_persistent_context(**kw)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(45000)
        if login_only:
            page.goto("https://studio.youtube.com/")
            log("sign in to Blessed Prayers in this window; close it when Studio shows the channel")
            page.wait_for_event("close", timeout=0)
            return 0
        failed = 0
        for mp4 in jobs:
            job = json.loads(mp4.with_suffix(".json").read_text(encoding="utf-8"))
            log("JOB", mp4.name)
            bad = gate(job)
            if bad:
                res = {"file": mp4.name, "error": bad}
            else:
                try:
                    res = upload_one(page, mp4, job)
                except (PWTimeout, RuntimeError, Exception) as e:
                    res = {"file": mp4.name, "error": str(e)[:400]}
                    page.screenshot(path=str(DONE / (mp4.stem + ".error.png")))
            ok = "error" not in res
            failed += 0 if ok else 1
            (DONE / (mp4.stem + (".result.json" if ok else ".FAILED.json"))).write_text(json.dumps(res, indent=1))
            if ok:
                for p in [mp4, mp4.with_suffix(".json")] + ([mp4.parent / job["thumbnail"]] if job.get("thumbnail") else []):
                    if p.exists():
                        shutil.move(str(p), str(DONE / p.name))
            log("RESULT", json.dumps(res)[:300])
        ctx.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
