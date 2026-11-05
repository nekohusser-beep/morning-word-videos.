#!/usr/bin/env python3
"""Scene Engine planner (steps 2-3 of the script-to-video pipeline).

  plan.py split   SCRIPT.txt SCENES.json [--wps 1.9] [--max-sec 8] [--title T] [--aspect 16:9|9:16]
  plan.py check   SCENES.json [--script SCRIPT.txt]
  plan.py prompts SCENES.json OUT_DIR

split   Cuts the approved script into scenes of at most 8 seconds of voice (1.9 words/s for the Kokoro voice at 0.95, 15 words; calibrate with the voice you use).
        The spoken text is fixed here, in code, so no AI step can rewrite or drop a line.
        Every 5th scene is marked 'abstract' (20% non-character graphics), scripture scenes too.
        An AI step (prompts/3_visual_planner.txt) then fills only the picture and motion fields.
check   Gate before any image is made or credit spent: spoken text unchanged, every scene has
        prompts, 20% abstract, banned phrases, future promises, off-limits wording.
prompts Writes one complete image prompt per scene (base style + character sheet + scene) and the
        motion prompts, one file each, so they can be fed to an image tool one at a time.
"""
import argparse, hashlib, json, os, re, sys

BANNED = [  # Neko's no-AI-jargon list (Oct 11, 2026); scripts must not contain these
    "sit with that", "hold that for a moment", "let that sink in", "read that again", "say it with me",
    "take a breath", "breathe", "here's the thing", "let's be honest", "real talk", "at the end of the day",
    "i see you", "you are enough", "give yourself grace", "speak life", "lean into", "lean in", "unpack",
    "journey", "navigate", "embrace", "unlock", "elevate", "empower", "resonate", "testament to", "tapestry",
    "delve", "in today's world", "fast-paced world", "picture this", "imagine this", "let's dive in",
    "buckle up", "game-changer", "game changer", "that's the whole verse", "that's the whole thing",
    "two words.", "six words.", "and that's okay", "show up for yourself",
]
PATTERNS = [  # (regex, label)
    (r"\bit'?s not about [^.]{1,60}, it'?s about\b", "'it's not about X, it's about Y'"),
    (r"\bnot just [^.]{1,60}, but\b", "'not just X, but Y'"),
    (r"\bno [a-z]+\. no [a-z]+\. just\b", "'No X. No Y. Just Z.'"),
]
PROMISES = [r"\btomorrow\b", r"\bnext week\b", r"\bnext episode\b", r"\bsee you (tomorrow|on monday|on tuesday|on wednesday|on thursday|on friday)\b",
            r"\bin tomorrow'?s\b", r"\bcoming up next\b"]
OFFLIMITS = [r"\bi pray over you\b", r"\bi declare\b", r"\bi release\b", r"\bthus saith the lord\b",
             r"\bgod told me\b", r"\bi feel led\b", r"\b(damn|hell yeah|crap|shit|fuck|bastard)\b",
             r"\bnot a clone\b"]
MOTIONS = ["push_in", "pull_out", "pan_right", "pan_left", "drift_up"]
DEFAULT_BASE = (
    "Hand-drawn stick-figure storybook illustration. Warm cream parchment background with soft paper grain. "
    "Thick, rounded, slightly uneven black ink lines. Stick figures have round white heads with two dot eyes, "
    "no nose, no mouth, simple limbs and plain flat-color robes. One accent color only: warm gold (#C8963E) "
    "for light, glory and sacred things. Flat shading, generous empty space, one clear focal subject per frame, "
    "simple ancient-world settings (desert, olive trees, stone houses, tents, hills, night sky). "
    "No text, no letters, no numbers, no logos, no watermark, no borders, no photorealism, no 3D.")


def norm(t):
    t = re.sub(r"[#*_`>]+", " ", t)
    t = t.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    return re.sub(r"\s+", " ", t).strip()


def words_of(t): return re.findall(r"[A-Za-z0-9'’:-]+", t.lower())


def sha(vos): return hashlib.sha256("\n".join(vos).encode()).hexdigest()[:16]


def sentences(text):
    """Split after . ! ? (keeping a closing quote with its sentence) when the next word starts a sentence."""
    out, cur = [], []
    toks = text.split()
    for k, t in enumerate(toks):
        cur.append(t)
        nxt = toks[k + 1] if k + 1 < len(toks) else ""
        if re.search(r"[.!?][\"']?$", t) and (not nxt or re.match(r"[\"']?[A-Z0-9]", nxt)): out.append(" ".join(cur)); cur = []
    if cur: out.append(" ".join(cur))
    return out


def clause_split(sent, cap):
    w = sent.split()
    if len(w) <= cap: return [sent]
    out = []
    while len(w) > cap:
        best = None
        for i in range(cap, 4, -1):  # prefer punctuation nearest the cap
            if re.search(r"[,;:—-]$", w[i - 1]): best = i; break
        if best is None: best = cap
        out.append(" ".join(w[:best])); w = w[best:]
    if w: out.append(" ".join(w))
    return out


def split(a):
    text = norm(open(a.script).read())
    cap = int(a.max_sec * a.wps)
    units = [u for s in sentences(text) for u in clause_split(s, cap)]
    scenes, cur = [], []
    for u in units:
        n = len(u.split())
        if cur and sum(len(x.split()) for x in cur) + n > cap:
            scenes.append(" ".join(cur)); cur = []
        cur.append(u)
    if cur: scenes.append(" ".join(cur))
    if len(scenes) > 1 and len(scenes[-1].split()) < 5 and len((scenes[-2] + " " + scenes[-1]).split()) <= cap:
        tail = scenes.pop(); scenes[-1] += " " + tail
    out = []
    for i, vo in enumerate(scenes):
        n = len(vo.split())
        scripture = bool(re.search(r"\b\d{1,3}:\d{1,3}\b", vo))
        kind = "abstract" if (i % 5 == 4 or scripture) else "character"
        out.append({"id": f"s{i+1:03d}", "vo": vo, "words": n, "est_sec": round(n / a.wps, 2), "kind": kind,
                    "chars": [], "image_prompt": "", "motion_prompt": "", "motion": MOTIONS[i % len(MOTIONS)]})
    need = -(-len(out) // 5)  # at least 20% abstract: add the scene farthest from the existing ones
    while sum(1 for x in out if x["kind"] == "abstract") < need:
        ab = [k for k, x in enumerate(out) if x["kind"] == "abstract"] or [-5]
        k = max((k for k, x in enumerate(out) if x["kind"] == "character" and k > 0), key=lambda k: (min(abs(k - j) for j in ab), k)) if len(out) > 2 else 0
        out[k]["kind"] = "abstract"
    d = {"title": a.title, "aspect": a.aspect, "wps": a.wps, "max_sec": a.max_sec, "script_sha": sha([s["vo"] for s in out]),
         "base_prompt": DEFAULT_BASE, "characters": {}, "scenes": out}
    json.dump(d, open(a.out, "w"), indent=1, ensure_ascii=False)
    ab = sum(1 for s in out if s["kind"] == "abstract")
    print(f"{len(out)} scenes, {sum(s['words'] for s in out)} words, est {sum(s['est_sec'] for s in out):.0f}s, "
          f"{ab} abstract ({100*ab//len(out)}%) -> {a.out}")


def check(a):
    d = json.load(open(a.scenes)); sc = d["scenes"]; err, warn = [], []
    cap = int(d["max_sec"] * d["wps"])
    if sha([s["vo"] for s in sc]) != d["script_sha"]: err.append("spoken text changed since split (script_sha mismatch): restore the original vo lines")
    if a.script:
        sw, vw = words_of(norm(open(a.script).read())), words_of(" ".join(s["vo"] for s in sc))
        if sw != vw: err.append(f"scene text does not match {a.script} word for word ({len(sw)} vs {len(vw)} words)")
    ab = 0
    for s in sc:
        i = s["id"]
        if s["words"] > cap: err.append(f"{i}: {s['words']} words, over {cap} (8 s)")
        if s["kind"] not in ("character", "abstract"): err.append(f"{i}: kind must be character or abstract")
        if s["kind"] == "abstract": ab += 1
        if len(s.get("image_prompt", "")) < 25: err.append(f"{i}: image_prompt missing")
        if len(s.get("motion_prompt", "")) < 8: err.append(f"{i}: motion_prompt missing")
        if s.get("motion") not in MOTIONS: err.append(f"{i}: motion must be one of {MOTIONS}")
        for c in s.get("chars", []):
            if c not in d.get("characters", {}): err.append(f"{i}: character '{c}' has no entry in characters")
        if s["kind"] == "abstract" and s.get("chars"): warn.append(f"{i}: abstract scene lists characters")
        lo = s["vo"].lower()
        for b in BANNED:
            if b in lo: err.append(f"{i}: banned phrase '{b}'")
        for rx, lab in PATTERNS:
            if re.search(rx, lo): err.append(f"{i}: banned pattern {lab}")
        for rx in PROMISES:
            if re.search(rx, lo): err.append(f"{i}: specific future promise ({rx})")
        for rx in OFFLIMITS:
            if re.search(rx, lo): err.append(f"{i}: off-limits wording ({rx})")
        if re.search(r"\b(text|words|letters|caption|sign that says)\b", s.get("image_prompt", "").lower()) and "no text" not in s["image_prompt"].lower():
            warn.append(f"{i}: image prompt asks for text; images must be text-free (captions are added later)")
    need = -(-len(sc) // 5)
    if ab < need: err.append(f"only {ab} abstract scenes, need at least {need} (20%)")
    if not d.get("base_prompt"): err.append("base_prompt empty")
    for e in err: print("ERROR", e)
    for w in warn: print("warn ", w)
    print(f"{len(sc)} scenes, {ab} abstract, {len(err)} errors, {len(warn)} warnings")
    sys.exit(1 if err else 0)


def prompts(a):
    d = json.load(open(a.scenes)); os.makedirs(a.out_dir, exist_ok=True)
    frame = "Frame: 16:9 landscape." if d.get("aspect", "16:9") == "16:9" else "Frame: 9:16 portrait."
    allp = []
    for s in d["scenes"]:
        parts = [d["base_prompt"], frame]
        for c in s.get("chars", []): parts.append(f"CHARACTER {c}: {d['characters'][c]}")
        parts.append("SCENE: " + s["image_prompt"])
        full = "\n".join(parts)
        open(os.path.join(a.out_dir, f"{s['id']}_image.txt"), "w").write(full)
        open(os.path.join(a.out_dir, f"{s['id']}_motion.txt"), "w").write(s["motion_prompt"])
        allp.append(f"=== {s['id']} ({s['kind']}) ===\n{full}\n--- motion: {s['motion_prompt']}\n")
    open(os.path.join(a.out_dir, "all.txt"), "w").write("\n".join(allp))
    print(f"{len(d['scenes'])} image prompts + motion prompts -> {a.out_dir}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(); sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("split"); s.add_argument("script"); s.add_argument("out"); s.add_argument("--wps", type=float, default=1.9)
    s.add_argument("--max-sec", dest="max_sec", type=float, default=8.0); s.add_argument("--title", default="")
    s.add_argument("--aspect", default="16:9", choices=["16:9", "9:16"]); s.set_defaults(f=split)
    c = sp.add_parser("check"); c.add_argument("scenes"); c.add_argument("--script"); c.set_defaults(f=check)
    q = sp.add_parser("prompts"); q.add_argument("scenes"); q.add_argument("out_dir"); q.set_defaults(f=prompts)
    a = p.parse_args(); a.f(a)
