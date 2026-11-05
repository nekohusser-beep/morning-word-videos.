#!/usr/bin/env python3
"""Instrumental bed via a local ACE-Step 1.5 REST server. Usage: run_bed.py <name> <outdir> <duration_s> <bpm> <caption_file>"""
import json, os, sys, time
from pathlib import Path
import requests
BASE = "http://127.0.0.1:8001"
name, out, dur, bpm, capf = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
out.mkdir(parents=True, exist_ok=True)
t0 = time.time()
def stamp(m): print(f"[{time.time()-t0:7.0f}s] {m}", flush=True)
for i in range(360):
    try:
        if requests.get(f"{BASE}/health", timeout=5).status_code == 200: break
    except Exception: pass
    if i % 12 == 0: stamp("waiting for server health")
    time.sleep(10)
else: sys.exit("server never became healthy")
stamp("server healthy")
body = {"prompt": open(capf, encoding="utf-8").read().strip(), "lyrics": "[Instrumental]", "thinking": False, "use_cot_caption": False,
        "use_cot_language": False, "vocal_language": "unknown", "audio_format": "mp3", "bpm": bpm, "key_scale": "D minor", "time_signature": "4",
        "audio_duration": dur, "inference_steps": 8, "batch_size": int(os.environ.get("TAKES", "2")), "use_random_seed": True}
tid = None
for attempt in range(1, 9):
    try:
        r = requests.post(f"{BASE}/release_task", json=body, timeout=120)
        print(attempt, r.status_code, r.text[:300], flush=True)
        if r.status_code == 200 and (r.json().get("data") or {}).get("task_id"):
            tid = r.json()["data"]["task_id"]; break
    except Exception as e: print(attempt, "EXC", repr(e), flush=True)
    time.sleep(30 * attempt)
if not tid: sys.exit("could not submit")
stamp(f"submitted {tid}")
res = None
for i in range(200):
    time.sleep(60)
    try: q = requests.post(f"{BASE}/query_result", json={"task_id_list": [tid]}, timeout=60).json()
    except Exception as e: stamp(f"poll {i+1}: transient {e!r}"); continue
    d = (q.get("data") or [{}])[0]; st = d.get("status"); stamp(f"poll {i+1}: status={st}")
    if st in (1, 2): res = d; break
if not res or res.get("status") != 1: sys.exit(f"failed: {str(res)[:500]}")
items = json.loads(res["result"])
for n, it in enumerate(items, 1):
    a = requests.get(BASE + it["file"], timeout=300); a.raise_for_status()
    (out / f"{name}-t{n}.mp3").write_bytes(a.content)
    stamp(f"saved {name}-t{n}.mp3 {len(a.content)} bytes")
