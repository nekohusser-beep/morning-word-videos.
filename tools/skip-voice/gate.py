#!/usr/bin/env python3
"""SKIP GATE (Neko Nov 26 2026). Nothing from Big Skip / Little Skip reaches Neko or the uploader without this.

  gate.py <ep_dir> <voices_dir> <video.mp4> <qa_report.md>

1. voice gate: every line vs the locked refs (voice_gate.py bars). Any FAIL = blocked.
2. QA: the report must be written by a reviewer that did not build the cut and must contain a line
   'VERDICT: PASS'. Anything else = blocked.
3. writes tools/yt-push/gate/<video name>.json. neko_ok stays empty until he has watched that exact file;
   yt_push.py refuses the upload while any of the three is missing.
Order of work this enforces: free draft (free stills + locked voices) -> gate -> Neko -> only then any credits."""
import json, os, subprocess, sys, hashlib
ep, voices, video, qa = sys.argv[1:5]
here = os.path.dirname(os.path.abspath(__file__)); repo = os.path.dirname(os.path.dirname(here))
r = subprocess.run([sys.executable, f"{here}/voice_gate.py", f"{ep}/lines.json", voices], capture_output=True, text=True)
print(r.stdout[-1500:])
vg = "PASS" if r.returncode == 0 else "FAIL"
txt = open(qa, encoding="utf-8").read() if os.path.exists(qa) else ""
q = "PASS" if "VERDICT: PASS" in txt else "FAIL"
rec = {"video": os.path.relpath(video, repo), "sha256": hashlib.sha256(open(video, "rb").read()).hexdigest(),
       "voice_gate": vg, "qa": q, "qa_report": os.path.relpath(qa, repo), "neko_ok": ""}
out = f"{repo}/tools/yt-push/gate/{os.path.basename(video)}.json"
os.makedirs(os.path.dirname(out), exist_ok=True); json.dump(rec, open(out, "w"), indent=1)
print(f"voice_gate={vg} qa={q} -> {out}")
sys.exit(0 if vg == q == "PASS" else 1)
