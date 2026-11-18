"""Pray with Papa: puppet render (stills, mouth flap from voice envelope, push-ins, 3-word captions, title bar).
Usage: python3 render.py audio   -> writes dialogue.wav + timing.json
       python3 render.py frames  -> raw RGB frames to stdout"""
import json, sys, math, subprocess, os
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SR = 1080, 1920, 30, 48000
V = "/home/claude/pray/v/"
ART = "/mnt/user-data/uploads/Claude-Work/"
LINES = [("joy", "Papa? How do you talk to God? Do I need big church words?"),
         ("papa", "Nope. Praying is just talking to God. Same way you talk to me."),
         ("joy", "Even in my pajamas?"),
         ("papa", "Especially in your pajamas. Here's a trick. Hold up three fingers."),
         ("papa", "One, thank Him. Two, tell Him what's in your heart. Three, ask Him for help."),
         ("joy", "Okay. Dear God, thank You for Papa."),
         ("joy", "I got scared of the dark today. Please help me be brave."),
         ("papa", "In Jesus' name."),
         ("joy", "Amen!"),
         ("papa", "See? God heard every word. The Bible says, never stop praying.")]
SHOT = ["wide", "wide", "joy", "papa", "papa", "joy", "joy", "wide", "wide", "wide"]
GAP = {4: 0.7, 6: 0.5, 7: 0.15}
LEAD = 0.25
# usable art regions (x0, y0, x1, y1) in 572x1024 source, 9:16
REG = {"wide": (40, 0, 529, 870), "joy": (80, 0, 569, 870), "papa": (84, 152, 488, 870)}
FILES = {"wide": "pray-wide.png", "joy": "pray-joy.png", "papa": "pray-papa2.png"}
# mouth (x, y, width) in source px
MOUTH = {"wide": {"papa": (252, 381, 30), "joy": (385, 470, 22)},
         "joy": {"joy": (325, 460, 44)}, "papa": {"papa": (292, 398, 40)}}
FACE = {"wide": (300, 420), "joy": (325, 400), "papa": (292, 360)}

def load(i):
    k = LINES[i][0]
    a, sr = sf.read(f"{V}{k}_u{i:03d}.wav")
    if a.ndim > 1: a = a.mean(1)
    if sr != SR:
        a = np.interp(np.linspace(0, len(a), int(len(a) * SR / sr), endpoint=False), np.arange(len(a)), a)
    nz = np.where(np.abs(a) > 0.01)[0]
    return a[max(0, nz[0] - 500):nz[-1] + 2400]

if sys.argv[1] == "audio":
    parts, starts, durs, t = [np.zeros(int(LEAD * SR))], [], [], LEAD
    for i in range(len(LINES)):
        a = load(i)
        starts.append(t); durs.append(len(a) / SR)
        parts.append(a); g = GAP.get(i, 0.3); parts.append(np.zeros(int(g * SR)))
        t += len(a) / SR + g
    parts.append(np.zeros(int(1.6 * SR)))
    full = np.concatenate(parts)
    full = full / (np.abs(full).max() + 1e-9) * 0.89
    sf.write("/home/claude/pray/dialogue.wav", full, SR)
    json.dump({"starts": starts, "durs": durs, "total": len(full) / SR}, open("/home/claude/pray/timing.json", "w"))
    print(len(full) / SR); sys.exit()

T = json.load(open("/home/claude/pray/timing.json"))
starts, durs, TOTAL = T["starts"], T["durs"], T["total"]
raw, _ = sf.read("/home/claude/pray/dialogue.wav")
hop = SR // FPS
nfr = int(math.ceil(TOTAL * FPS))
env = np.array([np.sqrt(np.mean(raw[k * hop:(k + 1) * hop] ** 2)) if k * hop < len(raw) else 0 for k in range(nfr)])
env = np.clip(env / (np.percentile(env[env > 0.005], 90) + 1e-9), 0, 1)
env = np.convolve(env, [0.25, 0.5, 0.25], mode="same")

SC = {}
arts = {}
for k, f in FILES.items():
    x0, y0, x1, y1 = REG[k]
    im = Image.open(ART + f).convert("RGB").crop((x0, y0, x1, y1))
    s = W / (x1 - x0)
    SC[k] = (s, x0, y0)
    arts[k] = im.resize((W, int(round((y1 - y0) * s))), Image.LANCZOS)

FB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
POP = ImageFont.truetype(FB, 84); TITLEF = ImageFont.truetype(FB, 58); ENDF = ImageFont.truetype(FB, 64); REFF = ImageFont.truetype(FB, 46)

def line_at(tt):
    for i in range(len(LINES)):
        if starts[i] <= tt < starts[i] + durs[i]:
            return i
    return None

def last_line(tt):
    return max([k for k in range(len(LINES)) if starts[k] <= tt] or [0])

def draw_mouth(img, shot, who, o):
    if who not in MOUTH[shot]:
        return
    s, x0, y0 = SC[shot]
    x, y, w = MOUTH[shot][who]
    x, y, w = (x - x0) * s, (y - y0) * s, w * s
    if o < 0.08:
        return
    d = ImageDraw.Draw(img)
    h = w * (0.10 + 0.45 * o)
    d.ellipse([x - w * 0.5, y - h * 0.45, x + w * 0.5, y + h * 0.55], fill=(60, 22, 20), outline=(35, 14, 10), width=max(2, int(w * 0.06)))
    if o > 0.4:
        d.chord([x - w * 0.28, y + h * 0.05, x + w * 0.28, y + h * 0.5], 0, 180, fill=(170, 80, 84))

def caption(img, tt):
    i = line_at(tt)
    if i is None:
        return
    ws = LINES[i][1].split()
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
        col = (255, 225, 40) if a0 + j == k else (255, 255, 255)
        d.text((xx, 1380), wd, font=POP, fill=col, stroke_width=9, stroke_fill=(0, 0, 0))
        xx += d.textlength(wd, font=POP)

def box(img, lines_, y, font, pad=30, gap=68):
    d = ImageDraw.Draw(img)
    bw = max(d.textlength(l, font=font) for l in lines_) + pad * 2
    bh = gap * len(lines_) + 36
    bx = (W - bw) / 2
    d.rounded_rectangle([bx, y, bx + bw, y + bh], radius=20, fill=(255, 255, 255), outline=(0, 0, 0), width=4)
    for n, l in enumerate(lines_):
        d.text(((W - d.textlength(l, font=font)) / 2, y + 16 + gap * n), l, font=font, fill=(0, 0, 0))

def frame(n):
    tt = n / FPS
    i = line_at(tt)
    li = i if i is not None else last_line(tt)
    shot = SHOT[li]
    base = arts[shot]
    p = min(1.0, (tt - starts[li]) / max(1.0, durs[li]))
    z = 1.0 + 0.05 * p + (0.10 if li in (3, 8) and p > 0.4 else 0)
    if li == 9 and tt > starts[9] + durs[9]:
        z = 1.05
    z *= 1.0 + 0.003 * math.sin(tt * 2.0)
    s, x0, y0 = SC[shot]
    fx, fy = (FACE[shot][0] - x0) * s, (FACE[shot][1] - y0) * s
    bh = base.height
    cw = W / z; ch = min(cw * H / W, bh)
    cw = ch * W / H
    cx = min(max(fx, cw / 2), W - cw / 2)
    cy = min(max(fy + 60, ch / 2), bh - ch / 2)
    img = base.copy()
    if i is not None:
        draw_mouth(img, shot, LINES[i][0], float(env[n] if n < len(env) else 0))
    img = img.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.BILINEAR)
    if tt < starts[9] + durs[9]:
        box(img, ["How do you talk to God? \U0001F64F".replace(" \U0001F64F", "")], 140, TITLEF)
    else:
        box(img, ["Never stop praying.", "1 Thessalonians 5:17 (ICB)"], 640, ENDF, gap=84)
    caption(img, tt)
    return img

if sys.argv[1] == "frames":
    out = sys.stdout.buffer
    for n in range(nfr):
        out.write(frame(n).tobytes())
elif sys.argv[1] == "still":
    frame(int(float(sys.argv[2]) * FPS)).save(sys.argv[3])
