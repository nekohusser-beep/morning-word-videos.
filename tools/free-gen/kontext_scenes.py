#!/usr/bin/env python3
"""Free scene stills by editing a reference image on HF ZeroGPU Spaces (FLUX.1 Kontext, Qwen-Image-Edit fallback).
usage: kontext_scenes.py <prompts.json> <outdir>
prompts.json: {"ref": repo path, "chain_from": first shot name (its output becomes the ref for later shots so Nia stays the same),
               "edits": {shot: instruction}}"""
import json, os, sys, shutil, time, traceback
from gradio_client import Client, handle_file
cfg = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
tok = os.environ.get("HF_TOKEN") or None
SPACES = [("black-forest-labs/FLUX.1-Kontext-Dev", "/infer"), ("Qwen/Qwen-Image-Edit", "/infer")]
clients = {}
def client(sp):
    if sp not in clients:
        clients[sp] = Client(sp, hf_token=tok)
        try: print(clients[sp].view_api(return_format="str", print_info=False)[:1500], flush=True)
        except Exception: pass
    return clients[sp]
def first_image(res):
    if isinstance(res, (list, tuple)):
        for r in res:
            p = first_image(r)
            if p: return p
    if isinstance(res, dict):
        for k in ("path", "image", "value"):
            if k in res: return first_image(res[k])
    if isinstance(res, str) and os.path.exists(res): return res
    return None
def edit(ref, prompt, seed):
    for sp, api in SPACES:
        for attempt in range(2):
            try:
                c = client(sp)
                if "Kontext" in sp:
                    res = c.predict(input_image=handle_file(ref), prompt=prompt, seed=seed, randomize_seed=False, guidance_scale=2.5, steps=28, api_name=api)
                else:
                    res = c.predict(image=handle_file(ref), prompt=prompt, seed=seed, randomize_seed=False, api_name=api)
                p = first_image(res)
                if p: return p, sp
                print("no image from", sp, res, flush=True)
            except Exception as e:
                print("FAIL", sp, attempt, repr(e)[:400], flush=True); time.sleep(10)
    return None, None
ref0 = cfg["ref"]; chain = None
for name, prompt in cfg["edits"].items():
    ref = chain if (chain and name != cfg.get("chain_from")) else ref0
    for seed in (11, 22):
        p, sp = edit(ref, prompt, seed)
        print(name, seed, sp, p, flush=True)
        if p:
            dst = f"{out}/{name}_{seed}{os.path.splitext(p)[1] or '.png'}"; shutil.copy(p, dst)
            if name == cfg.get("chain_from") and chain is None: chain = dst
