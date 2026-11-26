#!/usr/bin/env python3
"""Big Skip AT HOME renderer (one still per scene, free). usage: python home_render.py <ep_dir> <out.mp4>
<ep_dir>: lines.json, final/u###.wav, cfg.json with
  scenes {name: [line idx...]}, art {name: "art/file.jpg"}, side {name: {"skip": x, "nia": x}} (0-1 face x, optional),
  mouth {name: {"skip": [x, y, w], "nia": [x, y, w]}} (pixels on the 1144x2048 art, optional),
  hook_text, title [..], cap {idx: text}, punch [idx], gap {idx: s}, end_card.
FIRST 3 SECONDS: first word on frame 1, bold top-center hook words swap every ~1.2 s, a visual change every word (punch/zoom pulse)."""
import json, sys, math, os, subprocess, tempfile
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont

EP, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, SR = 1080, 1920, 30, 44100
AW, AH = 1144, 2048
lines = json.load(open(f"{EP}/lines.json")); cfg = json.load(open(f"{EP}/cfg.json"))
NL = len(lines)
GAP = {int(k): v for k, v in cfg.get("gap", {}).items()}
CAP = {int(k): v for k, v in cfg.get("cap", {}).items()}
PUNCH = set(cfg.get("punch", []))
CAPY = {int(k): v for k, v in cfg.get("cap_y_line", {}).items()}
SCENE_OF = {i: s for s, ids in cfg["scenes"].items() for i in ids}
SCENE_LAST = {ids[-1] for ids in cfg["scenes"].values()}

tmp = tempfile.mkdtemp()
starts, durs, parts, t = [], [], [], 0.0
SEGS = []
for i in range(NL):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{EP}/final/u{i:03d}.wav", "-ar", str(SR), "-ac", "1", f"{tmp}/r.wav"], check=True)
    a, _ = sf.read(f"{tmp}/r.wav")
    nz = np.where(np.abs(a) > 0.01)[0]
    a = a[max(0, nz[0] - (0 if i == 0 else 400)):nz[-1] + 2000]
    mp = cfg.get("max_pause")                   # optional: shorten any silence inside a line to this many seconds (no dead air mid-line)
    if mp:
        q = np.abs(a) > 0.012; idx = np.where(q)[0]; keep = np.ones(len(a), bool)
        for u, v in zip(idx[:-1], idx[1:]):
            if (v - u) / SR > mp: keep[u + int(mp * SR / 2):v - int(mp * SR / 2)] = False
        a = a[keep]
    a = a / (np.max(np.abs(a)) + 1e-9) * 0.85
    starts.append(t); durs.append(len(a) / SR)
    w_ = SR // 100; r_ = np.array([np.sqrt(np.mean(a[k:k + w_] ** 2)) for k in range(0, len(a) - w_, w_)]) > 0.02   # spoken phrases = runs of sound split by >= 0.15 s of quiet
    on = np.where(r_)[0]; sg = []
    if len(on):                                 # keep every quiet run >= 0.05 s as a candidate boundary: (start_s, end_s) of the quiet
        brk = [(on[k] + 1, on[k + 1]) for k in range(len(on) - 1) if on[k + 1] - on[k] > 5]
        sg = [(on[0] / 100, (on[-1] + 1) / 100, [(u / 100, v / 100) for u, v in brk])]
    SEGS.append(sg)
    g = GAP.get(i, 1.0 if i in SCENE_LAST else 0.28)
    if cfg.get("frame_align"):                  # next line starts exactly on a frame, so sound and cut land together
        nxt = math.ceil((t + len(a) / SR + g) * FPS - 1e-6) / FPS; g = nxt - t - len(a) / SR
    parts += [a, np.zeros(int(round(g * SR)))]
    t += len(a) / SR + g
END = cfg.get("end", 2.6)
TOTAL = t + END
raw = np.concatenate(parts + [np.zeros(int(END * SR))])
out_a = raw
if cfg.get("bed"):                              # optional room tone under the whole cut, so pauses and the end card are never digital silence
    rng = np.random.default_rng(7); nz_ = rng.standard_normal(len(raw) + SR)
    k = np.exp(-np.arange(400) / 60.0); k /= k.sum()                       # soft low-pass: a distant night hum, no hiss
    tone = np.convolve(nz_, k, mode="same")[:len(raw)]
    tone = tone / (np.sqrt(np.mean(tone ** 2)) + 1e-9) * cfg["bed"]
    fade = np.minimum(1, np.minimum(np.arange(len(raw)) / (0.05 * SR), (len(raw) - np.arange(len(raw))) / (0.4 * SR)))
    out_a = raw + tone * fade
if cfg.get("end_chime"):                        # optional soft two-note chime as the end card lands (no dead air under it)
    out_a = out_a.copy(); k0 = int((t + 0.3) * SR)
    for j, hz in enumerate((523.25, 783.99)):
        n_ = np.arange(int(1.6 * SR)); tone_ = (np.sin(2 * np.pi * hz * n_ / SR) + 0.3 * np.sin(4 * np.pi * hz * n_ / SR)) * np.exp(-n_ / (0.45 * SR)) * np.minimum(1, n_ / (0.01 * SR))
        a0_ = k0 + int(j * 0.18 * SR); m_ = min(len(tone_), len(out_a) - a0_); out_a[a0_:a0_ + m_] += tone_[:m_] * cfg["end_chime"]
    out_a[-int(0.15 * SR):] *= np.linspace(1, 0, int(0.15 * SR))
wav = f"{tmp}/dialogue.wav"; sf.write(wav, out_a, SR)
hop = SR // FPS; nfr = int(math.ceil(TOTAL * FPS))
env = np.array([np.sqrt(np.mean(raw[k * hop:(k + 1) * hop] ** 2)) if k * hop < len(raw) else 0 for k in range(nfr)])
env = env / (np.percentile(env[env > 0.005], 90) + 1e-9)

def line_at(tt):
    for i in range(NL):
        if starts[i] <= tt < starts[i] + durs[i]: return i
    return None
def last_line(tt): return max([k for k in range(NL) if starts[k] <= tt] or [0])

arts = {s: Image.open(os.path.join(EP, p)).convert("RGB").resize((AW, AH), Image.LANCZOS) for s, p in cfg["art"].items()}
SIDE = cfg.get("side", {}); MOUTH = cfg.get("mouth", {})
FB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
if not os.path.exists(FB): FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
POP, HOOK, TITLEF, ENDF = (ImageFont.truetype(FB, s) for s in (86, 104, 60, 74))

def draw_mouth(img, scene, who, openv):
    """[x, y, w] = old flap; [x, y, w, cw, ch] = cover the drawn mouth with sampled skin first, then a cartoon mouth
    (closed line / half / open with tongue, 3 steps so it reads as a cartoon flap)."""
    m = MOUTH.get(scene, {}).get(who)
    if not m: return
    d = ImageDraw.Draw(img)
    if len(m) == 3:
        if cfg.get("rest_mouths") and openv < 0.1: return      # silent: leave the mouth exactly as drawn in the art
        x, y, w = m; h = min(max(4, w * (0.12 + 0.75 * openv)), w * cfg.get("mouth_max", 1.0))
        d.ellipse([x - w * 0.55, y - h * 0.5, x + w * 0.55, y + h * 0.5], fill=(70, 10, 18), outline=(0, 0, 0), width=6); return
    x, y, w, cw, ch = m
    a = np.asarray(img)
    ring = [a[int(y + ch * 0.5 * math.sin(t)), int(x + cw * 0.5 * math.cos(t))] for t in np.linspace(0, 2 * math.pi, 48, endpoint=False)
            if 0 <= int(y + ch * 0.5 * math.sin(t)) < a.shape[0] and 0 <= int(x + cw * 0.5 * math.cos(t)) < a.shape[1]]
    ring = np.array(ring); ring = ring[ring.sum(1) > 300]          # skip dark outline pixels
    skin = tuple(int(v) for v in (np.median(ring, 0) if len(ring) else (245, 245, 245)))
    d.ellipse([x - cw / 2, y - ch / 2, x + cw / 2, y + ch / 2], fill=skin)
    lvl = 0 if openv < 0.18 else (1 if openv < 0.55 else 2)
    if lvl == 0:
        d.arc([x - w / 2, y - w * 0.06, x + w / 2, y + w * 0.06], 10, 170, fill=(0, 0, 0), width=6); return
    h = w * (0.5 if lvl == 1 else 0.85)
    box = [x - w * 0.5, y - h * 0.35, x + w * 0.5, y + h * 0.65]
    d.chord(box, 0, 180, fill=(60, 8, 14), outline=(0, 0, 0), width=6)       # D-shaped open mouth
    d.line([box[0], box[1] + (box[3] - box[1]) / 2, box[2], box[1] + (box[3] - box[1]) / 2], fill=(0, 0, 0), width=6)
    if lvl == 2:
        d.chord([x - w * 0.28, y + h * 0.2, x + w * 0.28, y + h * 0.62], 180, 360, fill=(215, 95, 100))
        d.rectangle([x - w * 0.36, y + h * 0.15 - 1, x + w * 0.36, y + h * 0.15 + w * 0.08], fill=(255, 255, 255))

def text_c(d, y, txt, font, fill=(255, 255, 255), sw=9):
    d.text(((W - d.textlength(txt, font=font)) / 2, y), txt, font=font, fill=fill, stroke_width=sw, stroke_fill=(0, 0, 0))

import re
def cap_words(i):
    """-> [(word, t_on, chunk_id)] for line i. Each sentence of the caption is tied to one spoken phrase (found from the pauses),
    so a caption never runs ahead of or behind the voice; chunks of up to 3 words never straddle two sentences."""
    txt = CAP.get(i, lines[i]["text"]); ph = [p for p in re.split(r"(?<=[.!?])\s+", txt) if p]
    v0, v1, brk = SEGS[i][0] if SEGS[i] else (0, durs[i], [])
    if len(ph) - 1 > len(brk) or i in cfg.get("cap_one", []): ph = [txt]     # cap_one: lines whose sentences run together with no real pause
    cut = sorted(sorted(brk, key=lambda q: q[0] - q[1])[:len(ph) - 1])           # the longest pauses are the sentence breaks
    sg = list(zip([v0] + [q[1] for q in cut], [q[0] for q in cut] + [v1]))
    out, cid = [], 0
    for p, (a0, a1) in zip(ph, sg):
        ws = p.split(); wt = np.cumsum([0] + [len(w) + 2 for w in ws]); wt = a0 + wt / wt[-1] * (a1 - a0)
        for j, w in enumerate(ws):
            if j and j % 3 == 0: cid += 1
            out.append((w, wt[j], cid))
        cid += 1
    return out
CW = {}
def caption(img, tt):
    i = line_at(tt)
    if i is None: return
    if i not in CW: CW[i] = cap_words(i); print("cap", i, [(w, round(float(starts[i] + t0), 2)) for w, t0, _ in CW[i]])
    cw = CW[i]; el = tt - starts[i]
    k = max([n for n, (_, t0, _) in enumerate(cw) if t0 <= el + 1e-6] or [0])
    idx = [n for n, c in enumerate(cw) if c[2] == cw[k][2]]; chunk = [cw[n][0] for n in idx]; d = ImageDraw.Draw(img)
    txt = " ".join(chunk).upper()
    POPF = POP
    while d.textlength(txt, font=POPF) > W - cfg.get("cap_margin", 80) and POPF.size > 48: POPF = ImageFont.truetype(FB, POPF.size - 4)
    xx = (W - d.textlength(txt, font=POPF)) / 2
    for j, w in enumerate(chunk):
        wd = w.upper() + (" " if j < len(chunk) - 1 else "")
        d.text((xx, CAPY.get(i, cfg.get("cap_y", 1380))), wd, font=POPF, fill=(255, 225, 40) if idx[j] == k else (255, 255, 255), stroke_width=9, stroke_fill=(0, 0, 0))
        xx += d.textlength(wd, font=POPF)

HOOKW = cfg.get("hook_text", "").split()
def top(img, tt):
    d = ImageDraw.Draw(img)
    if tt < cfg.get("hook_end", starts[1] - 1e-3 if cfg.get("frame_align") and NL > 1 else 3.6) and (HOOKW or cfg.get("hook_cards")):   # hook_end: set it to the first cut so the card never drops a frame early  # hook: bold top-center, swaps every 1.2 s
        n = min(len(HOOKW), 1 + int(tt / 1.2) * 2)
        hc = cfg.get("hook_cards")                 # optional: whole cards, one per 1.2 s, so every card reads on its own
        ht = hc[min(int(tt / 1.2), len(hc) - 1)] if hc else " ".join(HOOKW[:n][-3:]); hf = HOOK
        while d.textlength(ht, font=hf) > W - 60 and hf.size > 50: hf = ImageFont.truetype(FB, hf.size - 6)  # long words: shrink to fit
        text_c(d, 170, ht, hf, fill=tuple(cfg.get("hook_fill", (255, 225, 40))), sw=11)
        return
    if cfg.get("title_off"): return          # no standing title box (when the art carries its own sign)
    tl = cfg["title"]; bh = 70 * len(tl) + 40
    bw = max(d.textlength(l, font=TITLEF) for l in tl) + 60
    bx, by = (W - bw) / 2, 150
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=18, fill=(255, 255, 255), outline=(0, 0, 0), width=4)
    for n, l in enumerate(tl): d.text((bx + 30, by + 18 + 70 * n), l, font=TITLEF, fill=(0, 0, 0))

def frame(n):
    tt = n / FPS
    i = line_at(tt); li = i if i is not None else last_line(tt)
    scene = SCENE_OF[li]
    p = min(1.0, (tt - starts[li]) / max(1.0, durs[li]))
    who = lines[li]["kind"]
    z = 1.06 + 0.05 * p + (0.14 if li in PUNCH and p > 0.5 else 0)
    if tt < 3.0: z += 0.03 * (int(tt / 0.45) % 2)          # visual change every beat in the first 3 s
    z *= 1.0 + 0.004 * math.sin(tt * 2.1)
    fx = SIDE.get(scene, {}).get(who, 0.32 if who == "skip" else 0.68) * AW
    cyf = 0.42
    zm = cfg.get("zoom", {}).get(str(li))      # optional per-line shot: [zoom, y centre 0-1, x centre 0-1 (optional)] = a cut to a closer framing
    if zm:
        z = zm[0] * (1.0 + 0.04 * p) * (1.0 + 0.004 * math.sin(tt * 2.1)); cyf = zm[1]
        if len(zm) > 2: fx = zm[2] * AW
    cw, ch = AW / z, AW / z * (H / W)
    cx = min(max(fx, cw / 2), AW - cw / 2); cy = min(max(AH * cyf, ch / 2), AH - ch / 2)
    img = arts[scene].copy()
    mg = cfg.get("mouth_gate", 0.0)             # below this level the speaker's mouth stays shut (breaths and pauses inside a line)
    if cfg.get("rest_mouths"):                     # every character with a mouth spec gets the drawn mouth all the time (closed when silent)
        for w2 in MOUTH.get(scene, {}):
            ov_ = float(np.clip(env[n] if n < len(env) else 0, 0, 1)) if (i is not None and w2 == who) else 0.0
            draw_mouth(img, scene, w2, ov_ if ov_ >= mg else 0.0)
    elif i is not None: draw_mouth(img, scene, who, float(np.clip(env[n] if n < len(env) else 0, 0, 1)))
    img = img.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.BILINEAR)
    if tt > TOTAL - END + 0.3 and cfg.get("end_card"):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 150)); img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        d = ImageDraw.Draw(img); words = cfg["end_card"].replace("😂", "").split(); half = (len(words) + 1) // 2
        ey = cfg.get("end_y", 820); text_c(d, ey, " ".join(words[:half]).upper(), ENDF, fill=(255, 225, 40)); text_c(d, ey + 100, " ".join(words[half:]).upper(), ENDF)
        return img
    top(img, tt); caption(img, tt)
    return img

p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                      "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for n in range(nfr): p.stdin.write(frame(n).tobytes())
p.stdin.close(); p.wait()
print("TOTAL", round(TOTAL, 1), "s", nfr, "frames")
