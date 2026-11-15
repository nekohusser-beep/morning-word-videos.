#!/usr/bin/env python3
"""etsy_push.py - our own AnythingMCP for Etsy (Kingdom Impact Shop). Etsy Open API v3 on GitHub Actions.

What AnythingMCP did for us (Oct 10-17 2026 trial): Etsy API access - create/patch listings, add
images, add the digital file. Its trial died Oct 17 and the PDF upload was the one step Claude could
never do in a browser. This does those jobs, free, and runs in this public repo where Actions are free.

SECRETS: everything sensitive (Etsy app keys, the sign-in token, the PKCE verifier) lives in
tools/etsy-push/vault.enc, encrypted with the VAULT_KEY Actions secret. Product files (PDFs, images)
are stored encrypted as *.enc too, so nothing sellable is readable in this public repo.

JOBS: drop tools/etsy-push/queue/<name>.json (one job or a list) and push; the workflow applies it.
  {"cmd": "whoami"}
  {"cmd": "listings", "state": "active"}                     active | draft | inactive
  {"cmd": "get", "listing_id": 123}
  {"cmd": "create_draft", "fields": {"title": "...", "description": "...", "price": 9.99, "quantity": 999,
     "who_made": "i_did", "when_made": "made_to_order", "taxonomy_id": 2078, "type": "download", "tags": "a,b"}}
  {"cmd": "image_from_url", "listing_id": 123, "url": "https://...jpg", "rank": 2}
  {"cmd": "upload_file", "listing_id": 123, "file": "Third-Shift-Prayers.pdf"}      file = in files/
  {"cmd": "upload_image", "listing_id": 123, "file": "L1-cover.jpg", "rank": 1}
  {"cmd": "delete_image", "listing_id": 123, "image_id": 456}
  {"cmd": "patch", "listing_id": 123, "fields": {"title": "...", "tags": "a,b"}}
  {"cmd": "publish", "listing_id": 123}       refuses a digital listing with no file (Neko's Nov 6 rule)
MODES (workflow input): apply (default on push) | signin_link | signin_finish <redirect URL> | check
Exit: 0 ok, 1 a job failed, 2 missing vault/sign-in.
"""
import base64
import datetime as dt
import glob
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.parse

import requests
from cryptography.fernet import Fernet

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
VAULT = os.path.join(HERE, "vault.enc")
FILES = os.path.join(HERE, "files")
QUEUE = os.path.join(HERE, "queue")
DONE = os.path.join(QUEUE, "done")
REPORTS = os.path.join(REPO, "reports", "etsy-push")
API = "https://openapi.etsy.com/v3/application"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
SCOPES = "email_r shops_r listings_r listings_w listings_d transactions_r"


# ------------------------------------------------------------------ vault
def fernet(key=None):
    key = key or os.environ.get("VAULT_KEY", "").strip()
    if not key:
        print("No VAULT_KEY secret. Add it at github.com/nekohusser-beep/morning-word-videos./settings/secrets/actions")
        sys.exit(2)
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(("etsy-push|" + key).encode()).digest()))


def load_vault():
    return json.loads(fernet().decrypt(open(VAULT, "rb").read()))


def save_vault(v, msg="etsy-push: vault"):
    open(VAULT, "wb").write(fernet().encrypt(json.dumps(v).encode()))
    git_publish([os.path.relpath(VAULT, REPO)], msg)


def read_file(name):
    p = os.path.join(FILES, name + ".enc")
    if not os.path.exists(p):
        raise FileNotFoundError("tools/etsy-push/files/%s.enc not found" % name)
    return fernet().decrypt(open(p, "rb").read())


def git_publish(paths, msg):
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    run = lambda *c: subprocess.run(c, cwd=REPO)
    run("git", "config", "user.name", "etsy-push-bot")
    run("git", "config", "user.email", "noreply@github.com")
    run("git", "add", "-A", "--", *paths)
    if subprocess.run(["git", "commit", "-q", "-m", msg], cwd=REPO).returncode != 0:
        return
    for _ in range(5):
        run("git", "fetch", "-q", "--depth=20", "origin", "main")
        run("git", "rebase", "-q", "origin/main")
        if subprocess.run(["git", "push", "-q"], cwd=REPO).returncode == 0:
            return
        time.sleep(3)


# ------------------------------------------------------------------ sign-in
def signin_link(v):
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(12)
    v["pkce"] = {"verifier": verifier, "state": state, "made": int(time.time())}
    save_vault(v, "etsy-push: new sign-in link")
    url = "https://www.etsy.com/oauth/connect?" + urllib.parse.urlencode({
        "response_type": "code", "redirect_uri": v["redirect"], "scope": SCOPES,
        "client_id": v["keystring"], "state": state, "code_challenge": challenge,
        "code_challenge_method": "S256"}, quote_via=urllib.parse.quote)
    os.makedirs(REPORTS, exist_ok=True)
    open(os.path.join(REPORTS, "SIGN-IN-LINK.txt"), "w").write(url + "\n")
    git_publish([os.path.relpath(REPORTS, REPO)], "etsy-push: sign-in link")
    print("SIGN-IN LINK:", url)
    return 0


def signin_finish(v, landed_url):
    q = urllib.parse.parse_qs(urllib.parse.urlparse(landed_url.strip()).query)
    code, state = (q.get("code") or [""])[0], (q.get("state") or [""])[0]
    pk = v.get("pkce") or {}
    if not code:
        print("No ?code= in that address. Paste the whole address bar after tapping Allow.")
        return 2
    if state != pk.get("state"):
        print("That address is from an older sign-in link. Make a new link and try again.")
        return 2
    r = requests.post(TOKEN_URL, data={"grant_type": "authorization_code", "client_id": v["keystring"],
                                       "redirect_uri": v["redirect"], "code": code,
                                       "code_verifier": pk["verifier"]}, timeout=60)
    if r.status_code != 200:
        print("Etsy refused the code:", r.status_code, r.text[:300])
        return 2
    t = r.json()
    t["saved_at"] = int(time.time())
    v["token"], v["pkce"] = t, {}
    save_vault(v, "etsy-push: signed in")
    print("signed in; shop_id", Etsy(v).shop_id())
    return 0


# ------------------------------------------------------------------ api
class Etsy:
    def __init__(self, v):
        self.v = v
        self._shop = None

    def token(self):
        t = self.v.get("token")
        if not t:
            print("No Etsy sign-in yet: run the etsy-push workflow with mode signin_link.")
            sys.exit(2)
        if time.time() < t.get("saved_at", 0) + t.get("expires_in", 0) - 120:
            return t["access_token"]
        r = requests.post(TOKEN_URL, data={"grant_type": "refresh_token", "client_id": self.v["keystring"],
                                           "refresh_token": t["refresh_token"]}, timeout=60)
        if r.status_code != 200:
            print("Etsy sign-in expired or revoked:", r.status_code, r.text[:200])
            sys.exit(2)
        t = r.json()
        t["saved_at"] = int(time.time())
        self.v["token"] = t
        save_vault(self.v, "etsy-push: token rotated")  # Etsy rotates the refresh token on every use
        return t["access_token"]

    def h(self):
        return {"x-api-key": self.v["keystring"] + ":" + self.v["shared_secret"],
                "Authorization": "Bearer " + self.token()}

    def shop_id(self):
        if not self._shop:
            uid = self.token().split(".")[0]
            self._shop = requests.get("%s/users/%s/shops" % (API, uid), headers=self.h(), timeout=60).json()["shop_id"]
        return self._shop

    def call(self, method, path, **kw):
        r = requests.request(method, API + path, headers=self.h(), timeout=180, **kw)
        try:
            body = r.json()
        except Exception:
            body = {"raw": r.text[:500]}
        return r.status_code, body


def run_job(e, job):
    c, L = job.get("cmd"), job.get("listing_id")
    s = e.shop_id()
    if c == "whoami":
        return 200, {"shop_id": s}
    if c == "listings":
        st, b = e.call("GET", "/shops/%s/listings" % s, params={"state": job.get("state", "active"), "limit": 100})
        if st == 200:
            b = [{"listing_id": x["listing_id"], "title": x["title"], "state": x["state"],
                  "type": x.get("listing_type")} for x in b.get("results", [])]
        return st, b
    if c == "get":
        return e.call("GET", "/listings/%s" % L)
    if c == "create_draft":
        f = dict(job["fields"])
        f.setdefault("quantity", 999)
        f.setdefault("who_made", "i_did")
        f.setdefault("when_made", "made_to_order")
        f.setdefault("type", "download")
        st, b = e.call("POST", "/shops/%s/listings" % s, data=f)
        if 200 <= st < 300:
            b = {"listing_id": b.get("listing_id"), "state": b.get("state"), "url": b.get("url")}
        return st, b
    if c == "image_from_url":
        r = requests.get(job["url"], timeout=120)
        if r.status_code != 200:
            return r.status_code, {"error": "could not download the image"}
        name = os.path.basename(urllib.parse.urlparse(job["url"]).path) or "image.jpg"
        return e.call("POST", "/shops/%s/listings/%s/images" % (s, L),
                      files={"image": (name, r.content)}, data={"rank": job.get("rank", 1), "overwrite": "true"})
    if c == "upload_file":
        name = job["file"]
        return e.call("POST", "/shops/%s/listings/%s/files" % (s, L),
                      files={"file": (name, read_file(name))}, data={"name": job.get("name", name)})
    if c == "upload_image":
        name = job["file"]
        return e.call("POST", "/shops/%s/listings/%s/images" % (s, L),
                      files={"image": (name, read_file(name))},
                      data={"rank": job.get("rank", 1), "overwrite": "true"})
    if c == "delete_image":
        return e.call("DELETE", "/shops/%s/listings/%s/images/%s" % (s, L, job["image_id"]))
    if c == "patch":
        return e.call("PATCH", "/shops/%s/listings/%s" % (s, L), data=job["fields"])
    if c == "publish":
        st, info = e.call("GET", "/listings/%s" % L)
        if st != 200:
            return st, info
        if info.get("listing_type") == "download":
            fst, files = e.call("GET", "/shops/%s/listings/%s/files" % (s, L))
            if fst != 200 or not files.get("count"):
                return 409, {"refused": "digital listing has no file attached; it stays a draft (Neko's rule, Nov 6)"}
        return e.call("PATCH", "/shops/%s/listings/%s" % (s, L), data={"state": "active"})
    return 400, {"error": "unknown cmd %r" % c}


# ------------------------------------------------------------------ main
def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else "apply").lower()
    v = load_vault()
    if mode == "signin_link":
        return signin_link(v)
    if mode == "signin_finish":
        return signin_finish(v, sys.argv[2] if len(sys.argv) > 2 else os.environ.get("LANDED_URL", ""))
    e = Etsy(v)
    if mode == "check":
        print("vault ok; app", v["keystring"][:4] + "...", "; signed in:", bool(v.get("token")))
        if v.get("token"):
            print("shop_id", e.shop_id())
        return 0
    files = sorted(glob.glob(os.path.join(QUEUE, "*.json")))
    if not files:
        print("Nothing queued.")
        return 0
    os.makedirs(DONE, exist_ok=True)
    failed = 0
    for f in files:
        data = json.load(open(f, encoding="utf-8"))
        jobs = data if isinstance(data, list) else [data]
        results, ok = [], True
        for j in jobs:
            st, body = run_job(e, j)
            good = 200 <= st < 300
            ok &= good
            print("%s %s -> %s" % ("OK " if good else "BAD", json.dumps(j)[:120], st))
            if not good:
                print("   ", json.dumps(body)[:400])
            results.append({"job": j, "status": st, "result": body if not good or j["cmd"] in ("whoami", "listings", "create_draft") else "ok"})
            time.sleep(0.3)
        stamp = dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        name = os.path.basename(f)[:-5] + "-" + stamp + ("" if ok else ".FAILED") + ".json"
        json.dump({"jobs": jobs, "results": results}, open(os.path.join(DONE, name), "w"), indent=1)
        if ok:
            os.remove(f)
        else:
            failed += 1
    git_publish([os.path.relpath(QUEUE, REPO)], "etsy-push applied")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
