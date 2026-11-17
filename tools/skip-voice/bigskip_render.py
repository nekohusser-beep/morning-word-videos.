#!/usr/bin/env python3
"""Big Skip (coworker series, Skip + Dre) renderer for break-room episodes. Same look as Ep 'Ate My Lunch' (ep2b).
usage: python bigskip_render.py <ep_dir> <out.mp4>
<ep_dir> needs lines.json, final/u###.wav (one per line, from skip-voice-fast) and cfg.json:
  {"title": ["When your coworker", "..."], "wide": [0,1,...], "punch": [...], "gap": {"12": 0.9}, "cap": {"5": "caption text"}}
Art: ep2b/build/{breakroom,dre_table,skip_fridge}.jpg."""
import json, sys, math, os, subprocess, tempfile
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont

EP, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "ep2b/build/")
W, H, FPS, SR = 1080, 1920, 30, 44100
lines = json.load(open(f"{EP}/lines.json"))
cfg = json.load(open(f"{EP}/cfg.json"))
NL = len(lines)
GAP = {int(k): v for k, v in cfg.get("gap", {}).items()}
CAP = {int(k): v for k, v in cfg.get("cap", {}).items()}
WIDE = set(cfg.get("wide", [0, 1]))
PUNCH = set(cfg.get("punch", []))

# ---- stitch dialogue
tmp = tempfile.mkdtemp()
starts, durs, parts = [], [], []
t = 0.0
for i in range(NL):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{EP}/final/u{i:03d}.wav", "-ar", str(SR), "-ac", "1", f"{tmp}/r.wav"], check=True)
    a, _ = sf.read(f"{tmp}/r.wav")
    nz = np.where(np.abs(a) > 0.01)[0]
    a = a[max(0, nz[0] - 400):nz[-1] + 2000]
    a = a / (np.max(np.abs(a)) + 1e-9) * 0.85
    starts.append(t); durs.append(len(a) / SR)
    g = GAP.get(i, 0.28)
    parts += [a, np.zeros(int(g * SR))]
    t += len(a) / SR + g
TOTAL = t + 0.6
raw = np.concatenate(parts + [np.zeros(int(0.6 * SR))])
wav = f"{tmp}/dialogue.wav"; sf.write(wav, raw, SR)
hop = SR // FPS
nfr = int(math.ceil(TOTAL * FPS))
env = np.array([np.sqrt(np.mean(raw[k * hop:(k + 1) * hop] ** 2)) if k * hop < len(raw) else 0 for k in range(nfr)])
env = env / (np.percentile(env[env > 0.005], 90) + 1e-9)

def line_at(tt):
    for i in range(NL):
        if starts[i] <= tt < starts[i] + durs[i]:
            return i
    return None

MOUTH = {"breakroom": {"skip": (165, 445, 26), "dre": (445, 505, 20)}, "dre_table": {"dre": (295, 532, 44)}, "skip_fridge": {"skip": (332, 505, 70)}}
FACE = {"breakroom": (300, 470), "dre_table": (290, 470), "skip_fridge": (330, 460)}
SKIN = {"breakroom": (250, 250, 250), "dre_table": (255, 255, 255), "skip_fridge": (252, 252, 252)}
def last_line(tt):
    return max([k for k in range(NL) if starts[k] <= tt] or [0])
def shot_for(tt):
    i = line_at(tt)
    i = last_line(tt) if i is None else i
    if i in WIDE:
        return "breakroom"
    return "dre_table" if lines[i]["kind"] == "dre" else "skip_fridge"

S = 2.0
arts = {k: Image.open(ART + k + ".jpg").convert("RGB").resize((1144, 2048), Image.LANCZOS) for k in MOUTH}
POP = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", 86)
TITLEF = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", 60)
try:
    EMO = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
    emoji = Image.new("RGBA", (140, 140), (0, 0, 0, 0)); ImageDraw.Draw(emoji).text((0, 0), "\U0001F62D", font=EMO, embedded_color=True)
    emoji = emoji.crop(emoji.getbbox()).resize((62, 62), Image.LANCZOS)
except Exception:
    emoji = None

def draw_mouth(img, shot, who, openv):
    if who not in MOUTH.get(shot, {}):
        return
    x, y, w = (v * S for v in MOUTH[shot][who])
    d = ImageDraw.Draw(img)
    if who == "skip":
        d.ellipse([x - w * 0.75, y - w * 0.32, x + w * 0.75, y + w * 0.32], fill=SKIN[shot])
    h = max(4, w * (0.12 + 0.75 * openv))
    d.ellipse([x - w * 0.55, y - h * 0.5, x + w * 0.55, y + h * 0.5], fill=(70, 10, 18), outline=(0, 0, 0), width=int(3 * S))
    if openv > 0.35:
        d.chord([x - w * 0.32, y, x + w * 0.32, y + h * 0.48], 180, 360, fill=(220, 90, 100))
        d.chord([x - w * 0.32, y + h * 0.05, x + w * 0.32, y + h * 0.48], 0, 180, fill=(220, 90, 100))

def caption(img, tt):
    i = line_at(tt)
    if i is None:
        return
    ws = CAP.get(i, lines[i]["text"]).split()
    wt = np.cumsum([len(w) + 2 for w in ws]); wt = wt / wt[-1] * durs[i]
    k = min(int(np.searchsorted(wt, tt - starts[i])), len(ws) - 1)
    a0 = (k // 3) * 3
    chunk = ws[a0:a0 + 3]
    d = ImageDraw.Draw(img)
    txt = " ".join(chunk).upper()
    while d.textlength(txt, font=POP) > W - 80 and len(chunk) > 1:
        chunk = chunk[:-1]; txt = " ".join(chunk).upper()
    xx = (W - d.textlength(txt, font=POP)) / 2
    for j, w in enumerate(chunk):
        wd = w.upper() + (" " if j < len(chunk) - 1 else "")
        d.text((xx, 1320), wd, font=POP, fill=(255, 225, 40) if a0 + j == k else (255, 255, 255), stroke_width=9, stroke_fill=(0, 0, 0))
        xx += d.textlength(wd, font=POP)

def title(img):
    d = ImageDraw.Draw(img)
    tl = cfg["title"]
    bh = 70 * len(tl) + 40
    bw = max(d.textlength(l, font=TITLEF) for l in tl) + 60 + (80 if emoji else 0)
    bx, by = (W - bw) / 2, 150
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=18, fill=(255, 255, 255), outline=(0, 0, 0), width=4)
    for n, l in enumerate(tl):
        d.text((bx + 30, by + 18 + 70 * n), l, font=TITLEF, fill=(0, 0, 0))
    if emoji:
        img.paste(emoji, (int(bx + bw - 90), int(by + bh - 62 - 22)), emoji)

def frame(n):
    tt = n / FPS
    shot = shot_for(tt)
    i = line_at(tt)
    li = i if i is not None else last_line(tt)
    p = min(1.0, (tt - starts[li]) / max(1.0, durs[li]))
    z = 1.0 + 0.04 * p + (0.12 if li in PUNCH and p > 0.55 else 0)
    z *= 1.0 + 0.004 * math.sin(tt * 2.1)
    fx, fy = (v * S for v in FACE[shot])
    cw, ch = 1144 / z, 1144 / z * (H / W)
    cx = min(max(fx, cw / 2), 1144 - cw / 2) if z > 1.001 else 572
    cy = min(max(fy + 80, ch / 2), 2048 - ch / 2)
    img = arts[shot].copy()
    if i is not None:
        draw_mouth(img, shot, lines[i]["kind"], float(np.clip(env[n] if n < len(env) else 0, 0, 1)))
    img = img.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.BILINEAR)
    title(img)
    caption(img, tt)
    return img

p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                      "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for n in range(nfr):
    p.stdin.write(frame(n).tobytes())
p.stdin.close(); p.wait()
print("TOTAL", round(TOTAL, 1), "s", nfr, "frames")
