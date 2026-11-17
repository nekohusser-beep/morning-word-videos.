#!/usr/bin/env python3
"""desk-poster / from_chrome.py - reuse Neko's own Chrome sign-in (Blessed Prayers) so he never signs in again.
Chrome won't let automation drive its own default profile, so this copies the sign-in parts of his Chrome
profile (Local State + Network cookies + Preferences) into desk-poster\\profile, then checks Studio opens as
Blessed Prayers. Chrome must be closed while copying (it locks the cookie file): it is closed politely and
reopened with its tabs right after. Tries each Chrome profile, most recently used first, until one works."""
import json, os, shutil, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

CHANNEL = "UCaKI8Xsi-MHu78UnJTY1xpg"
HOME = Path(os.environ.get("DESK_POSTER_HOME", Path.home() / "Desktop" / "Claude-Work" / "desk-poster"))
PROFILE = HOME / "profile"
UD = Path(os.environ["LOCALAPPDATA"]) / "Google" / "Chrome" / "User Data"
CHROME = next((p for p in [Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Google/Chrome/Application/chrome.exe",
                           Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
                           Path(os.environ["LOCALAPPDATA"]) / "Google/Chrome/Application/chrome.exe"] if p.exists()), None)


def log(*a):
    line = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(HOME / "uploader.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def chrome_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/NH"], capture_output=True, text=True).stdout
    return "chrome.exe" in out


def close_chrome():
    if not chrome_running():
        return False
    log("closing your Chrome for a few seconds to copy the sign-in (it reopens with your tabs)")
    subprocess.run(["taskkill", "/IM", "chrome.exe"], capture_output=True)
    for _ in range(20):
        time.sleep(1)
        if not chrome_running():
            return True
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
    time.sleep(2)
    return True


def copy_profile(name):
    if PROFILE.exists():
        shutil.rmtree(PROFILE, ignore_errors=True)
    dst = PROFILE / "Default"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(UD / "Local State", PROFILE / "Local State")
    src = UD / name
    for f in ("Preferences", "Secure Preferences", "Login Data", "Web Data"):
        if (src / f).exists():
            shutil.copy2(src / f, dst / f)
    if (src / "Network").exists():
        shutil.copytree(src / "Network", dst / "Network", dirs_exist_ok=True)
    elif (src / "Cookies").exists():
        shutil.copy2(src / "Cookies", dst / "Cookies")


def test(pw):
    ctx = pw.chromium.launch_persistent_context(user_data_dir=str(PROFILE), channel="chrome", headless=False,
                                                viewport={"width": 1366, "height": 860},
                                                args=["--disable-blink-features=AutomationControlled"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(45000)
    try:
        page.goto("https://studio.youtube.com/channel/%s/videos" % CHANNEL, wait_until="domcontentloaded")
        page.wait_for_timeout(12000)
        url, title = page.url, page.title()
        text = page.inner_text("body")[:4000] if "studio.youtube.com" in url else ""
        ok = "studio.youtube.com" in url and CHANNEL in url and "Blessed Prayers" in (text + title)
        page.screenshot(path=str(HOME / "studio-check.png"))
        return ok, url, title
    finally:
        ctx.close()


def main():
    HOME.mkdir(parents=True, exist_ok=True)
    if not CHROME or not (UD / "Local State").exists():
        log("FROM-CHROME FAIL: Chrome not found"); return 2
    state = json.loads((UD / "Local State").read_text(encoding="utf-8"))
    cache = state.get("profile", {}).get("info_cache", {})
    names = sorted(cache, key=lambda n: -float(cache[n].get("active_time", 0) or 0)) or ["Default"]
    log("Chrome profiles:", ", ".join("%s (%s)" % (n, cache.get(n, {}).get("name", "")) for n in names))
    was_open = close_chrome()
    copied = {}
    for n in names:
        try:
            copy_profile(n)
            tmp = HOME / ("_copy_" + n.replace(" ", "_"))
            shutil.rmtree(tmp, ignore_errors=True)
            shutil.copytree(PROFILE, tmp)
            copied[n] = tmp
        except Exception as e:
            log("copy failed for", n, str(e)[:200])
    if was_open:
        subprocess.Popen([str(CHROME), "--restore-last-session"])
        log("your Chrome is back open")
    result = 1
    with sync_playwright() as pw:
        for n, tmp in copied.items():
            shutil.rmtree(PROFILE, ignore_errors=True)
            shutil.copytree(tmp, PROFILE)
            try:
                ok, url, title = test(pw)
            except Exception as e:
                ok, url, title = False, "error", str(e)[:200]
            log("profile", n, "->", "BLESSED PRAYERS OK" if ok else "not it", url[:120], title[:60])
            if ok:
                (PROFILE / "signed_in.txt").write_text(time.strftime("%Y-%m-%d %H:%M") + " from Chrome profile " + n, encoding="utf-8")
                result = 0
                break
    for tmp in copied.values():
        shutil.rmtree(tmp, ignore_errors=True)
    if result:
        shutil.rmtree(PROFILE, ignore_errors=True)
        log("FROM-CHROME FAIL: no Chrome profile opened Studio as Blessed Prayers")
    else:
        log("FROM-CHROME OK: uploader now uses your Chrome sign-in")
    return result


if __name__ == "__main__":
    sys.exit(main())
