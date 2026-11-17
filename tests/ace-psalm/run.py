#!/usr/bin/env python3
"""Drive a local ACE-Step 1.5 REST server (documented API: /health, /release_task, /query_result, /v1/audio).
Usage: run.py <short|full> <outdir>. Writes <outdir>/<case>.mp3, <case>-task.json, <case>-timing.txt. Exit 1 on failure."""
import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from lyrics import CAPTION, CASES, lyrics_for  # noqa: E402

BASE = "http://127.0.0.1:8001"
case, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
t0 = time.time()


def stamp(msg):
    print(f"[{time.time() - t0:7.0f}s] {msg}", flush=True)


# 1) wait for the server (it downloads the model weights on first start)
for i in range(60 * 60 // 10):
    try:
        if requests.get(f"{BASE}/health", timeout=5).status_code == 200:
            break
    except Exception:
        pass
    if i % 12 == 0:
        stamp("waiting for server health")
    time.sleep(10)
else:
    sys.exit("server never became healthy")
t_up = time.time() - t0
stamp("server healthy")

# 2) submit: DiT only (thinking off), one sample, exact KJV lyrics
body = {
    "prompt": CASES[case].get("caption", CAPTION),
    "lyrics": lyrics_for(case, os.environ.get("ACE_FLOW", "verse")),
    "thinking": False,
    "use_cot_caption": False,
    "use_cot_language": False,
    "vocal_language": "en",
    "audio_format": "mp3",
    "bpm": 60,
    "key_scale": "D minor",
    "time_signature": "4",
    "audio_duration": CASES[case]["duration"],
    "inference_steps": 8,
    "batch_size": int(os.environ.get("TAKES", "1")),
    "use_random_seed": True,
}
# retry the submit: right after /health the server can still answer 5xx while it lazy-loads; every failure is written to <case>-run-error.txt
tid = None
for attempt in range(1, 9):
    try:
        r = requests.post(f"{BASE}/release_task", json=body, timeout=120)
        print(attempt, r.status_code, r.text[:400], flush=True)
        if r.status_code == 200 and (r.json().get("data") or {}).get("task_id"):
            tid = r.json()["data"]["task_id"]
            break
        with open(out / f"{case}-run-error.txt", "a", encoding="utf-8") as fh:
            fh.write(f"submit try {attempt}: HTTP {r.status_code} {r.text[:600]}\n")
    except Exception as e:  # noqa: BLE001
        print(attempt, "EXC", repr(e), flush=True)
        with open(out / f"{case}-run-error.txt", "a", encoding="utf-8") as fh:
            fh.write(f"submit try {attempt}: {e!r}\n")
    time.sleep(30 * attempt)
if not tid:
    sys.exit("could not submit the task after 8 tries (see run-error.txt)")
t_sub = time.time()
stamp(f"submitted {tid}")

# 3) poll
res = None
for i in range(150):
    time.sleep(60)
    try:
        q = requests.post(f"{BASE}/query_result", json={"task_id_list": [tid]}, timeout=60).json()
    except Exception as e:  # noqa: BLE001
        stamp(f"poll {i + 1}: transient {e!r}")
        continue
    d = (q.get("data") or [{}])[0]
    st = d.get("status")
    stamp(f"poll {i + 1}: status={st}")
    if st in (1, 2):
        res = d
        break
if not res:
    sys.exit("timed out waiting for the task")
(out / f"{case}-task.json").write_text(json.dumps(res, indent=1)[:20000], encoding="utf-8")
if res.get("status") != 1:
    sys.exit(f"task failed: {str(res)[:600]}")
t_gen = time.time() - t_sub

# 4) download
items = json.loads(res["result"])
f = items[0]["file"]
a = requests.get(BASE + f, timeout=300)
a.raise_for_status()
(out / f"{case}.mp3").write_bytes(a.content)
if len(items) > 1:  # several takes: keep every one so the checker can pick the best
    for n, it in enumerate(items, 1):
        r2 = requests.get(BASE + it["file"], timeout=300)
        r2.raise_for_status()
        (out / f"{case}-t{n}.mp3").write_bytes(r2.content)
(out / f"{case}-timing.txt").write_text(
    f"case={case} audio_seconds_requested={CASES[case]['duration']} server_ready_s={t_up:.0f} generate_s={t_gen:.0f} "
    f"takes={len(items)} bytes={len(a.content)}\nfile={f}\nmetas={items[0].get('metas')}\ngeneration_info={items[0].get('generation_info')}\n",
    encoding="utf-8",
)
stamp(f"saved {case}.mp3 ({len(a.content)} bytes); generate took {t_gen:.0f}s for {CASES[case]['duration']}s of audio")
