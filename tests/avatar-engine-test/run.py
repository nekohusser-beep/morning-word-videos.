#!/usr/bin/env python3
"""Derrick avatar-engine proof test (Oct 28 2026).

ONE still (ref/derrick-surrender-ref.jpg) + ONE audio cut (Psalm 51:10-12 from the locked
Oct 25 Hailuo build) go into Hedra Character-3 and Runway avatar_videos, untouched.
Single attempt per engine, no retries after a successful submit (spend guard).

Reads secrets from env: HEDRA_API_KEY, RUNWAY_API_KEY. Never prints them.
Writes everything to tests/avatar-engine-test/out/. Clips are named clip_A / clip_B in
random order (key.json holds the answer) so Neko ranks by eye, not by brand.

Usage: python tests/avatar-engine-test/run.py [--engines hedra,runway] [--prep-only]
"""
import argparse
import base64
import difflib
import json
import os
import pathlib
import random
import re
import subprocess
import sys
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "out"
STILL = pathlib.Path("ref/derrick-surrender-ref.jpg")
SRC = pathlib.Path("shorts/derrick/create-in-me-a-clean-heart-psalm-51.mp4")
KJV = (
    "Create in me a clean heart, O God; and renew a right spirit within me. "
    "Cast me not away from thy presence; and take not thy holy spirit from me. "
    "Restore unto me the joy of thy salvation; and uphold me with thy free spirit."
)
MAX_AUDIO_S = 25.0          # spend guard: never send more than this
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "medium.en")
POLL_LIMIT_S = 25 * 60
HEDRA = "https://api.hedra.com"
RUNWAY = "https://api.dev.runwayml.com"
RUNWAY_VERSION = "2024-11-06"
PRESET_VOICE = "vincent"    # required by the avatar record; unused because speech is our own audio

_whisper = None


def log(*a):
    print(*a, flush=True)


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def norm(text):
    return re.findall(r"[a-z']+", text.lower().replace("’", "'"))


def whisper_words(path):
    global _whisper
    from faster_whisper import WhisperModel
    if _whisper is None:
        _whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    segs, _ = _whisper.transcribe(str(path), word_timestamps=True, language="en", vad_filter=False)
    words = []
    for s in segs:
        for w in s.words:
            toks = norm(w.word)
            if toks:
                words.append({"w": " ".join(toks), "s": round(w.start, 3), "e": round(w.end, 3)})
    return words


def word_error_rate(ref, hyp):
    """Levenshtein over words. Returns (errors, ref_len)."""
    d = list(range(len(hyp) + 1))
    for i in range(1, len(ref) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(hyp) + 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (ref[i - 1] != hyp[j - 1]))
            prev = cur
    return d[len(hyp)], len(ref)


def find_span(words, ref):
    """Locate the KJV verse reading inside the source transcript. Returns (i, j) word indexes."""
    W = [x["w"] for x in words]
    best = None
    n = len(ref)
    for i in range(len(W)):
        if W[i:i + 4] != ref[:4]:
            continue
        for j in range(min(len(W), i + n + 12), max(i + n - 12, i + 1), -1):
            if W[j - 2:j] == ref[-2:]:
                score = difflib.SequenceMatcher(None, W[i:j], ref).ratio()
                if best is None or score > best[0]:
                    best = (score, i, j)
                break
    if best is None:
        raise RuntimeError("verse reading not found in source transcript")
    return best[1], best[2], best[0]


def prep_audio():
    """Cut the Psalm 51:10-12 reading out of the locked build as one lossless 48 kHz mono WAV."""
    OUT.mkdir(parents=True, exist_ok=True)
    full = OUT / "source_full.wav"
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(SRC), "-vn", "-ac", "1", "-ar", "48000", str(full)])
    words = whisper_words(full)
    (OUT / "source_transcript.json").write_text(json.dumps(words))
    ref = norm(KJV)
    i, j, score = find_span(words, ref)
    t0 = max(0.0, words[i]["s"] - 0.30)
    t1 = words[j - 1]["e"] + 0.40
    wav = OUT / "test.wav"
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(full), "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}",
        "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(wav)])
    dur = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)]).stdout)
    if dur > MAX_AUDIO_S:
        raise RuntimeError(f"audio cut is {dur:.1f}s, over the {MAX_AUDIO_S}s spend guard")
    errs, n = word_error_rate(ref, [w["w"] for w in words[i:j]])
    info = {"start_s": round(t0, 3), "end_s": round(t1, 3), "duration_s": round(dur, 3),
            "ref_words": n, "source_cut_word_errors": errs, "span_similarity": round(score, 4)}
    log("audio prep:", info)
    return wav, info


def b64(path):
    return base64.b64encode(pathlib.Path(path).read_bytes()).decode()


def short(r):
    t = (r.text or "")[:600].replace("\n", " ")
    return f"HTTP {r.status_code}: {t}"


def find_urls(obj, out=None):
    out = [] if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v.startswith("http"):
                out.append((k, v))
            else:
                find_urls(v, out)
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, str) and v.startswith("http"):
                out.append(("item", v))
            else:
                find_urls(v, out)
    return out


def pick_video_url(obj):
    urls = find_urls(obj)
    for k, u in urls:
        if ".mp4" in u.split("?")[0].lower():
            return u
    for k, u in urls:
        if k in ("url", "download_url", "video_url", "signed_url"):
            return u
    return urls[0][1] if urls else None


def download(url, dest):
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)


# ---------------------------------------------------------------- Hedra Character-3
def run_hedra(key, wav):
    res = {"engine": "hedra", "model": "hedra-character-3", "resolution": "720p"}
    hdr = {"Authorization": f"Bearer {key}"}

    def upload(path):
        for scheme in ("Bearer", "Key"):
            hdr["Authorization"] = f"{scheme} {key}"
            with open(path, "rb") as f:
                r = requests.post(f"{HEDRA}/v3/files", headers=hdr, files={"file": f}, timeout=180)
            if r.status_code != 401:
                break
        if r.status_code >= 300:
            raise RuntimeError("hedra upload " + short(r))
        return r.json()["url"]

    img_url = upload(STILL)
    aud_url = upload(wav)
    body = {
        "input": {
            "prompt": ("A man speaking directly to the camera in a calm, warm, unhurried voice. "
                       "Steady locked camera, natural small head movements and blinks, relaxed shoulders. "
                       "Keep his face, hair, goatee, clothing and the room exactly as in the photo. No new objects."),
            "aspect_ratio": "9:16",
            "resolution": "720p",
            "start_image": {"source": "url", "url": img_url},
            "audio": {"source": "url", "url": aud_url},
        },
        "webhook": None,
        "idempotency_key": f"derrick-test-{os.environ.get('GITHUB_RUN_ID', 'local')}",
    }
    hdr["Content-Type"] = "application/json"
    try:
        e = requests.post(f"{HEDRA}/v3/models/hedra-character-3/estimate", headers=hdr, json=body, timeout=60)
        res["estimate"] = e.json() if e.status_code < 300 else short(e)
        log("hedra estimate:", res["estimate"])
    except Exception as ex:  # estimate is advisory only
        res["estimate"] = f"estimate failed: {ex}"
    t0 = time.time()
    r = requests.post(f"{HEDRA}/v3/models/hedra-character-3", headers=hdr, json=body, timeout=120)
    if r.status_code >= 300:
        raise RuntimeError("hedra submit " + short(r))
    job = r.json()["job_id"]
    res["job_id"] = job
    status = {}
    while time.time() - t0 < POLL_LIMIT_S:
        time.sleep(10)
        s = requests.get(f"{HEDRA}/v3/jobs/{job}/status", headers=hdr, timeout=60)
        status = s.json() if s.status_code < 300 else {"status": "HTTP%d" % s.status_code}
        st = str(status.get("status", "")).upper()
        log("hedra", st, status.get("progress"))
        if st in ("COMPLETED", "FAILED", "CANCELLED"):
            break
    if str(status.get("status", "")).upper() != "COMPLETED":
        raise RuntimeError(f"hedra did not complete: {json.dumps(status)[:500]}")
    j = requests.get(f"{HEDRA}/v3/jobs/{job}", headers=hdr, timeout=60).json()
    res["job"] = {k: v for k, v in j.items() if k != "outputs"}
    res["outputs_keys"] = [list(o.keys()) for o in j.get("outputs", []) if isinstance(o, dict)]
    url = pick_video_url(j.get("outputs", j))
    if not url:
        raise RuntimeError("hedra finished but no video URL found in outputs")
    dest = OUT / "raw_hedra.mp4"
    download(url, dest)
    res["seconds_to_generate"] = round(time.time() - t0)
    res["file"] = str(dest)
    return res


# ---------------------------------------------------------------- Runway avatar_videos
def run_runway(key, wav):
    res = {"engine": "runway", "model": "gwm1_avatars"}
    hdr = {"Authorization": f"Bearer {key}", "X-Runway-Version": RUNWAY_VERSION, "Content-Type": "application/json"}
    try:
        o = requests.get(f"{RUNWAY}/v1/organization", headers=hdr, timeout=60)
        res["org_before"] = o.json() if o.status_code < 300 else short(o)
        log("runway org before:", json.dumps(res["org_before"])[:400])
    except Exception as ex:
        res["org_before"] = f"org lookup failed: {ex}"
    t0 = time.time()
    avatar = None
    for processing in ("none", "optimize"):
        r = requests.post(f"{RUNWAY}/v1/avatars", headers=hdr, timeout=180, json={
            "name": "Derrick test",
            "referenceImage": "data:image/jpeg;base64," + b64(STILL),
            "personality": "A warm, steady Bible teacher who speaks calmly and prays with compassion.",
            "voice": {"type": "runway-live-preset", "presetId": PRESET_VOICE},
            "imageProcessing": processing,
        })
        if r.status_code < 300:
            avatar = r.json()
            res["image_processing"] = processing
            break
        log("runway avatar create failed:", short(r))
        res.setdefault("avatar_errors", []).append(short(r))
    if not avatar:
        raise RuntimeError("runway avatar create failed: " + " | ".join(res["avatar_errors"]))
    aid = avatar["id"]
    res["avatar_id"] = aid
    status = avatar.get("status")
    while status not in ("READY", "FAILED") and time.time() - t0 < 600:
        time.sleep(5)
        g = requests.get(f"{RUNWAY}/v1/avatars/{aid}", headers=hdr, timeout=60).json()
        status = g.get("status")
        log("runway avatar", status)
    if status != "READY":
        raise RuntimeError(f"runway avatar not ready: {status}")
    speech_uris = ["data:audio/wav;base64," + b64(wav)]
    task = None
    for uri in speech_uris:
        r = requests.post(f"{RUNWAY}/v1/avatar_videos", headers=hdr, timeout=180, json={
            "model": "gwm1_avatars",
            "avatar": {"type": "custom", "avatarId": aid},
            "speech": {"type": "audio", "audio": uri},
        })
        if r.status_code < 300:
            task = r.json()["id"]
            break
        res["submit_error"] = short(r)
        log("runway submit failed:", res["submit_error"])
    if not task:
        raise RuntimeError("runway avatar_videos submit failed: " + res.get("submit_error", "?"))
    res["task_id"] = task
    t1 = time.time()
    t = {}
    while time.time() - t1 < POLL_LIMIT_S:
        time.sleep(6)
        g = requests.get(f"{RUNWAY}/v1/tasks/{task}", headers=hdr, timeout=60)
        t = g.json() if g.status_code < 300 else {"status": "HTTP%d" % g.status_code}
        log("runway", t.get("status"), t.get("progress"))
        if t.get("status") in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
    res["cost"] = t.get("cost")
    res["estimatedCost"] = t.get("estimatedCost")
    if t.get("status") != "SUCCEEDED":
        raise RuntimeError(f"runway task not succeeded: {json.dumps(t)[:500]}")
    url = pick_video_url(t.get("output"))
    if not url:
        raise RuntimeError("runway succeeded but no output URL")
    dest = OUT / "raw_runway.mp4"
    download(url, dest)
    try:
        o = requests.get(f"{RUNWAY}/v1/organization", headers=hdr, timeout=60)
        res["org_after"] = o.json() if o.status_code < 300 else short(o)
    except Exception:
        pass
    res["seconds_to_generate"] = round(time.time() - t0)
    res["file"] = str(dest)
    return res


# ---------------------------------------------------------------- gates (numbers only; Neko's eye decides)
def probe(path):
    j = json.loads(sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]).stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), {})
    num, den = (v.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    return {"width": v.get("width"), "height": v.get("height"),
            "fps": round(float(num) / max(float(den), 1), 2), "duration_s": round(float(j["format"]["duration"]), 3),
            "audio_codec": a.get("codec_name"), "audio_rate": a.get("sample_rate"), "has_audio": bool(a)}


def pcm(path, sr=16000):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype("float32")


def envelope(x, sr=16000, frame=0.02):
    import numpy as np
    n = int(sr * frame)
    k = len(x) // n
    return np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(axis=1) + 1e-9)


def audio_match(a_path, b_path):
    import numpy as np
    ea, eb = envelope(pcm(a_path)), envelope(pcm(b_path))
    best = (-1.0, 0)
    for lag in range(-25, 26):
        x, y = (ea[lag:], eb) if lag >= 0 else (ea, eb[-lag:])
        m = min(len(x), len(y))
        if m < 50:
            continue
        c = float(np.corrcoef(x[:m], y[:m])[0, 1])
        if c > best[0]:
            best = (c, lag)
    return {"envelope_corr": round(best[0], 4), "lag_s": round(best[1] * 0.02, 2)}


def face_metrics(path):
    """Best-effort head motion / blinks. Proxies only, flagged as such."""
    try:
        import cv2
        import mediapipe as mp
        import numpy as np
    except Exception as e:
        return {"error": f"mediapipe unavailable: {e}"}
    try:
        fm = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)
        cap = cv2.VideoCapture(str(path))
        yaw, pitch, ear, frames, seen = [], [], [], 0, 0
        while True:
            ok, f = cap.read()
            if not ok:
                break
            frames += 1
            if frames % 2:
                continue
            r = fm.process(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
            if not r.multi_face_landmarks:
                continue
            seen += 1
            lm = r.multi_face_landmarks[0].landmark
            P = lambda i: np.array([lm[i].x, lm[i].y])
            l, rr, nose, chin, brow = P(33), P(263), P(1), P(152), P(10)
            w = np.linalg.norm(rr - l) + 1e-6
            yaw.append((nose[0] - (l[0] + rr[0]) / 2) / w)
            pitch.append((nose[1] - (brow[1] + chin[1]) / 2) / (np.linalg.norm(chin - brow) + 1e-6))
            e = (np.linalg.norm(P(160) - P(144)) + np.linalg.norm(P(158) - P(153))) / (2 * np.linalg.norm(P(33) - P(133)) + 1e-6)
            ear.append(float(e))
        cap.release()
        if not ear:
            return {"error": "no face found", "frames": frames}
        e = np.array(ear)
        closed = e < 0.72 * np.median(e)
        blinks = int(((closed[1:]) & (~closed[:-1])).sum())
        return {"frames_read": frames, "face_frames": seen,
                "yaw_std_proxy": round(float(np.std(yaw)), 4), "pitch_std_proxy": round(float(np.std(pitch)), 4),
                "blinks": blinks}
    except Exception as ex:
        return {"error": str(ex)}


def contact_sheet(path, dest):
    dur = probe(path)["duration_s"]
    try:
        sh(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-vf", f"fps=6/{max(dur, 1):.3f},scale=240:-2,tile=6x1",
            "-frames:v", "1", str(dest)])
    except Exception as ex:
        log("contact sheet failed:", ex)


def gate(res, wav):
    p = pathlib.Path(res["file"])
    g = {"probe": probe(p)}
    g["audio_vs_input"] = audio_match(wav, p)
    ref = norm(KJV)
    hyp = [w["w"] for w in whisper_words(p)]
    errs, n = word_error_rate(ref, hyp)
    g["whisper_word_errors"] = errs
    g["ref_words"] = n
    g["whisper_text"] = " ".join(hyp)
    g["face"] = face_metrics(p)
    g["duration_vs_audio_s"] = round(g["probe"]["duration_s"] - probe(wav)["duration_s"], 3)
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engines", default="hedra,runway")
    ap.add_argument("--prep-only", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    wav, audio_info = prep_audio()
    results = {"audio": audio_info, "engines": {}, "started": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}
    if a.prep_only:
        (OUT / "prep.json").write_text(json.dumps(results, indent=2))
        (OUT / "source_full.wav").unlink(missing_ok=True)
        log("PREP DONE", audio_info)
        return
    keys = {"hedra": os.environ.get("HEDRA_API_KEY", ""), "runway": os.environ.get("RUNWAY_API_KEY", "")}
    runners = {"hedra": run_hedra, "runway": run_runway}
    made = []
    for name in [e.strip() for e in a.engines.split(",") if e.strip()]:
        if not keys.get(name):
            results["engines"][name] = {"engine": name, "error": "no API key secret set; skipped"}
            continue
        try:
            r = runners[name](keys[name], wav)
            r["gate"] = gate(r, wav)
            made.append(name)
        except Exception as ex:
            r = {"engine": name, "error": str(ex)[:900]}
            log(name, "FAILED:", r["error"])
        results["engines"][name] = r
    order = made[:]
    random.shuffle(order)
    key = {}
    for idx, name in enumerate(order):
        label = "AB"[idx]
        dest = OUT / f"clip_{label}.mp4"
        dest.write_bytes(pathlib.Path(results["engines"][name]["file"]).read_bytes())
        contact_sheet(dest, OUT / f"sheet_{label}.jpg")
        key[label] = name
    (OUT / "key.json").write_text(json.dumps(key))
    results["finished"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    (OUT / "results.json").write_text(json.dumps(results, indent=2, default=str))
    # raw_* files are the same bytes as clip_A/B; drop them and the big source wav to keep the repo small
    for f in ("raw_hedra.mp4", "raw_runway.mp4", "source_full.wav"):
        (OUT / f).unlink(missing_ok=True)
    log("DONE", key)


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        import traceback
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "error.txt").write_text(traceback.format_exc())
        raise
