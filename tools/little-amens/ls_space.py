"""Try free HF Spaces for audio-driven lip sync. usage: ls_space.py video.mp4 audio.wav outdir [space ...]"""
import sys, os, json, shutil, time, traceback, urllib.request
from gradio_client import Client, handle_file
V, A, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(OUT, exist_ok=True)
TOK = os.environ.get("HF_TOKEN") or None
spaces = sys.argv[4:]
if not spaces:
    for q in ("latentsync", "musetalk", "lipsync", "lip sync"):
        try:
            d = json.load(urllib.request.urlopen(f"https://huggingface.co/api/spaces?search={q.replace(' ','%20')}&sort=likes&direction=-1&limit=12&full=true"))
            for s in d:
                st = (s.get("runtime") or {}).get("stage"); hw = ((s.get("runtime") or {}).get("hardware") or {}).get("current")
                print("SPACE", s["id"], s.get("likes"), st, hw, flush=True)
                if st == "RUNNING" and s["id"] not in spaces: spaces.append(s["id"])
        except Exception as e: print("search fail", q, e)
rep = []
for sp in spaces[:14]:
    r = {"space": sp}; t0 = time.time()
    try:
        c = Client(sp, hf_token=TOK) if TOK else Client(sp)
        api = c.view_api(return_format="dict"); eps = api.get("named_endpoints", {})
        r["endpoints"] = {k: [(p.get("parameter_name"), (p.get("python_type") or {}).get("type"), p.get("component")) for p in v.get("parameters", [])] for k, v in eps.items()}
        print(sp, json.dumps(r["endpoints"])[:1500], flush=True)
        done = False
        for name, ep in eps.items():
            ps = ep.get("parameters", []); comps = [p.get("component", "") for p in ps]
            if not (any("Video" in x for x in comps) and any("Audio" in x for x in comps)): continue
            if any("Image" in x for x in comps) and sum("Video" in x for x in comps) == 0: continue
            kw = {}
            for p in ps:
                n = p.get("parameter_name"); comp = p.get("component", "")
                if "Video" in comp: kw[n] = {"video": handle_file(V)}
                elif "Audio" in comp: kw[n] = handle_file(A)
                elif p.get("parameter_has_default"): continue
                else: kw[n] = p.get("parameter_default")
            print("CALL", sp, name, list(kw), flush=True)
            res = c.predict(api_name=name, **kw)
            print("RES", str(res)[:400], flush=True)
            def find(o):
                if isinstance(o, str) and os.path.exists(o) and o.lower().endswith((".mp4", ".webm", ".mov")): return o
                if isinstance(o, dict):
                    for v in o.values():
                        f = find(v)
                        if f: return f
                if isinstance(o, (list, tuple)):
                    for v in o:
                        f = find(v)
                        if f: return f
            f = find(res)
            if f:
                dst = os.path.join(OUT, sp.replace("/", "__") + ".mp4"); shutil.copy(f, dst); r["ok"] = dst; done = True; break
        if not done and "ok" not in r: r["note"] = "no usable endpoint or no file"
    except Exception as e:
        r["err"] = (str(e) or repr(e))[:600]; traceback.print_exc()
    r["sec"] = round(time.time() - t0); rep.append(r); print("DONE", json.dumps({k: v for k, v in r.items() if k != "endpoints"}), flush=True)
json.dump(rep, open(os.path.join(OUT, "report.json"), "w"), indent=1)
