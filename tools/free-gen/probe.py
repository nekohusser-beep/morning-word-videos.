#!/usr/bin/env python3
"""Free video-generator probe. Runs on a GitHub Actions runner (which can reach the open internet) and tries
each candidate in candidates.json: Hugging Face Spaces via gradio_client (auto-discovers the endpoint),
no-key HTTP endpoints, and the HF serverless inference API. Writes out/report.json and saves every file
produced to out/<candidate>/ so a human can judge the quality.

  probe.py candidates.json out [--prompt "..."] [--image path] [--per-sec 600]
Env: HF_TOKEN (optional; raises ZeroGPU quota when present)."""
import argparse, json, os, sys, time, traceback, shutil, urllib.request, urllib.parse, mimetypes

ap = argparse.ArgumentParser(); ap.add_argument("cands"); ap.add_argument("out")
ap.add_argument("--prompt", default="A simple colorful cartoon stick figure walking across green hills at sunrise, flat 2D animation, smooth motion")
ap.add_argument("--image", default="")
ap.add_argument("--per-sec", type=int, default=600)
A = ap.parse_args()
os.makedirs(A.out, exist_ok=True)
C = json.load(open(A.cands))
HF = os.environ.get("HF_TOKEN") or None
REPORT = []


def log(*a): print(time.strftime("%H:%M:%S"), *a, flush=True)


def keep(cand, src, tag="out"):
    """Copy a produced file (or dict with 'video'/'path'/'url') into out/<cand>/."""
    d = os.path.join(A.out, cand); os.makedirs(d, exist_ok=True)
    if isinstance(src, dict):
        for k in ("video", "path", "url", "image"):
            if k in src and src[k]: return keep(cand, src[k], tag)
        return None
    if isinstance(src, (list, tuple)):
        return [keep(cand, s, f"{tag}{i}") for i, s in enumerate(src)]
    if not isinstance(src, str): return None
    if src.startswith("http"):
        ext = os.path.splitext(urllib.parse.urlparse(src).path)[1] or ".bin"
        dst = os.path.join(d, tag + ext); urllib.request.urlretrieve(src, dst)
        if ext == ".m3u8":  # streamed chunks -> one mp4
            mp4 = os.path.join(d, tag + ".mp4")
            if os.system(f'ffmpeg -v error -y -protocol_whitelist file,http,https,tcp,tls -i "{src}" -c copy "{mp4}"') == 0: return mp4
        return dst
    if os.path.exists(src):
        dst = os.path.join(d, tag + os.path.splitext(src)[1]); shutil.copy(src, dst); return dst
    return None


def space_status(sid):
    try:
        req = urllib.request.Request(f"https://huggingface.co/api/spaces/{sid}", headers={"Authorization": f"Bearer {HF}"} if HF else {})
        j = json.load(urllib.request.urlopen(req, timeout=30))
        return j.get("runtime", {}).get("stage"), j.get("runtime", {}).get("hardware", {}).get("current")
    except Exception as e:
        return f"ERR {e}", None


def pick_endpoint(info):
    """Choose the endpoint that takes a prompt (and an image if we have one)."""
    best = None
    for name, ep in info.get("named_endpoints", {}).items():
        params = ep.get("parameters", [])
        labels = " ".join((p.get("label") or p.get("parameter_name") or "").lower() for p in params)
        score = ("prompt" in labels) * 2 + (A.image != "" and ("image" in labels)) * 2 + (ep.get("returns") and 1 or 0)
        if any(k in name.lower() for k in ("generate", "infer", "predict", "run", "video", "process")): score += 1
        if score and (best is None or score > best[0]): best = (score, name, ep)
    return best


def fill_args(ep):
    args = []
    for p in ep.get("parameters", []):
        lab = ((p.get("label") or "") + " " + (p.get("parameter_name") or "")).lower()
        comp = (p.get("component") or "").lower(); ex = p.get("example_input"); default = p.get("parameter_default")
        if "negative" in lab: args.append("blurry, low quality, text, watermark, distorted")
        elif "prompt" in lab and comp in ("textbox", "textarea", ""): args.append(A.prompt)
        elif comp in ("image", "imageeditor") or ("image" in lab and comp != "checkbox"):
            if A.image:
                from gradio_client import handle_file
                args.append(handle_file(A.image))
            else: args.append(None)
        elif "seed" in lab and comp in ("number", "slider"): args.append(42)
        elif "random" in lab and comp == "checkbox": args.append(False)
        elif default is not None and p.get("parameter_has_default"): args.append(default)
        elif ex is not None: args.append(ex)
        elif comp in ("number", "slider"): args.append(0)
        elif comp == "checkbox": args.append(False)
        else: args.append(None)
    return args


def try_space(c):
    from gradio_client import Client, handle_file
    global A
    if c.get("prompt"): A.prompt = c["prompt"]
    sid = c["space"]; stage, hw = space_status(sid); log(sid, "stage", stage, "hw", hw)
    row = {"name": c["name"], "space": sid, "stage": stage, "hardware": hw}
    if stage not in ("RUNNING", "RUNNING_APP_STARTING", "RUNNING_BUILDING", None) and not str(stage).startswith("ERR"):
        row["result"] = f"not running ({stage})"; return row
    t0 = time.time()
    try: cl = Client(sid, token=HF, verbose=False)
    except TypeError: cl = Client(sid, hf_token=HF, verbose=False)
    info = cl.view_api(return_format="dict", print_info=False)
    row["endpoints"] = list(info.get("named_endpoints", {}).keys())
    ep = pick_endpoint(info)
    if not ep: row["result"] = "no usable endpoint"; return row
    name, spec = ep[1], ep[2]; args = fill_args(spec)
    if c.get("api_name"): name = c["api_name"]
    if c.get("args"): args = [handle_file(A.image) if a == "@IMAGE" else a for a in c["args"]]
    row["api_name"] = name; row["args"] = [str(a)[:60] for a in args]
    job = cl.submit(*args, api_name=name)
    while not job.done():
        if time.time() - t0 > A.per_sec: row["result"] = f"timeout after {A.per_sec}s"; return row
        time.sleep(5)
    res = job.result()
    row["seconds"] = round(time.time() - t0, 1)
    saved = keep(c["name"], res if not isinstance(res, tuple) else list(res))
    row["files"] = saved; row["result"] = "OK" if saved else f"no file in result: {str(res)[:200]}"
    return row


def try_http(c):
    row = {"name": c["name"], "url": c["url"]}; t0 = time.time()
    url = c["url"].replace("{prompt}", urllib.parse.quote(A.prompt))
    req = urllib.request.Request(url, headers=c.get("headers", {}), data=json.dumps(c["json"]).encode() if c.get("json") else None)
    if c.get("json"): req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=A.per_sec) as r:
        ct = r.headers.get("Content-Type", ""); data = r.read()
    row["seconds"] = round(time.time() - t0, 1); row["content_type"] = ct; row["bytes"] = len(data)
    ext = mimetypes.guess_extension(ct.split(";")[0]) or ".bin"
    d = os.path.join(A.out, c["name"]); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "out" + ext); open(p, "wb").write(data); row["files"] = p
    row["result"] = "OK" if len(data) > 2000 and not ct.startswith("text/html") else f"small/odd response: {data[:200]!r}"
    return row


def try_hf_inference(c):
    row = {"name": c["name"], "model": c["model"]}; t0 = time.time()
    url = f"https://router.huggingface.co/hf-inference/models/{c['model']}"
    req = urllib.request.Request(url, data=json.dumps({"inputs": A.prompt}).encode(), headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {HF}"} if HF else {})})
    try:
        with urllib.request.urlopen(req, timeout=A.per_sec) as r: ct = r.headers.get("Content-Type", ""); data = r.read()
    except urllib.error.HTTPError as e:
        row["result"] = f"HTTP {e.code}: {e.read()[:300]!r}"; return row
    row["seconds"] = round(time.time() - t0, 1); row["content_type"] = ct; row["bytes"] = len(data)
    ext = mimetypes.guess_extension(ct.split(";")[0]) or ".bin"
    d = os.path.join(A.out, c["name"]); os.makedirs(d, exist_ok=True); p = os.path.join(d, "out" + ext); open(p, "wb").write(data)
    row["files"] = p; row["result"] = "OK" if len(data) > 2000 else f"odd: {data[:200]!r}"; return row


for c in C:
    log("==>", c["name"])
    try:
        row = {"space": try_space, "http": try_http, "hf_inference": try_hf_inference}[c["type"]](c)
    except Exception as e:
        row = {"name": c["name"], "result": f"ERROR {type(e).__name__}: {str(e)[:400]}"}
        log(traceback.format_exc()[-800:])
    row["type"] = c["type"]; REPORT.append(row); log(json.dumps(row)[:600])
    json.dump(REPORT, open(os.path.join(A.out, "report.json"), "w"), indent=1)

ok = [r["name"] for r in REPORT if r.get("result") == "OK"]
print("\nWORKING:", ok or "none")
