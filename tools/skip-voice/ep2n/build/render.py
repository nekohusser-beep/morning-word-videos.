"""Skip Ep 2 'Six O'Clock' puppet render (same engine as Ep 1): Gemini stills, mouth flap from the voice track,
push-ins + punch-ins, 3-word captions with the current word in yellow, white title bar.
Usage: python render.py mix            -> builds /home/claude/ep2/dialogue.wav + timing.json
       python render.py -1 0           -> prints frame count
       python render.py A B | ffmpeg    -> raw RGB frames A..B to stdout"""
import json, sys, math, os, subprocess
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SR = 1080, 1920, 30, 44100
WORK = "/home/claude/ep2/"
ART = WORK + "art/"
lines = json.load(open(os.path.join(os.path.dirname(__file__), "..", "lines.json")))
N = len(lines)
# captions use real spelling and digits (QC: every number on screen matches the script)
CAP = {0: "5:59. Good morning, Dre.", 1: "Bro. Why is there a lawn chair in my driveway?", 2: "Because the bank opens at 6. And so does my hand.", 4: "$40.", 8: "Week 1: $5. Week 2: $5. Week 3: $5. Week 4: see week 3.",
       10: "That's 8 weeks for $40. You'll be done paying me in January.", 14: "Real friends pay at 6. It's 6:02.",
       15: "Fine. You want it right now. Here you go. Paid in full.", 17: "That's a $40 gift card, man. We good. Enjoy your breakfast.",
       18: "See? Was that so hard? Thank you, Dre.", 19: "Balance... $3.12", 20: "DRE!"}
GAP = {17: 0.5, 18: 2.0}
DROP = {9}                          # "See? Structure." cut: no take matched Dre's voice            # beat before 'thank you' lands; time cut + phone ding before the balance
SHOT = {0: "driveway", 1: "driveway", 2: "skip_chair", 3: "dre_napkin", 4: "skip_chair", 5: "dre_napkin",
        6: "skip_chair", 7: "dre_napkin", 8: "skip_chair", 9: "dre_napkin", 10: "skip_chair", 11: "dre_napkin",
        12: "skip_chair", 13: "dre_napkin", 14: "skip_chair", 15: "dre_card", 16: "skip_chair", 17: "dre_card",
        18: "skip_chair", 19: "skip_phone", 20: "skip_phone"}
# mouth (x, y, width) in the 572x1024 stills
MOUTH = {"driveway": {"skip": (166, 446, 30), "dre": (425, 461, 16)}, "skip_chair": {"skip": (285, 432, 30)},
         "skip_phone": {"skip": (265, 505, 40)}, "dre_napkin": {"dre": (324, 447, 26)}, "dre_card": {"dre": (322, 450, 30)}}
FACE = {"driveway": (300, 450), "skip_chair": (285, 380), "skip_phone": (265, 430), "dre_napkin": (300, 420), "dre_card": (320, 420)}
PUNCH = {4, 6, 10, 14, 16, 20}
TIMING = WORK + "timing.json"


def build_mix():
    tmp = f"/tmp/r{os.getpid()}.wav"
    parts, starts, durs, t = [], [], [], 0.6
    out = np.zeros(int(SR * 0.6))
    for i in range(N):
        if i in DROP:
            starts.append(t); durs.append(0.0); continue
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{WORK}final/u{i:03d}.wav", "-ar", str(SR), "-ac", "1", tmp], check=True)
        a, _ = sf.read(tmp)
        nz = np.where(np.abs(a) > 0.01)[0]
        a = a[max(0, nz[0] - 400):nz[-1] + 2000]
        a = a / (np.max(np.abs(a)) + 1e-9) * 0.85
        starts.append(t); durs.append(len(a) / SR)
        g = GAP.get(i, 0.28)
        out = np.concatenate([out, a, np.zeros(int(SR * g))])
        t += len(a) / SR + g
    out = np.concatenate([out, np.zeros(int(SR * 1.0))])
    # phone ding in the time-cut gap before line 19
    d0 = int((starts[19] - 1.1) * SR)
    tt = np.arange(int(SR * 0.6)) / SR
    ding = (np.sin(2 * np.pi * 1318.5 * tt) + 0.5 * np.sin(2 * np.pi * 1975.5 * tt)) * np.exp(-tt * 7) * 0.35
    out[d0:d0 + len(ding)] += ding
    sf.write(WORK + "dialogue.wav", out, SR)
    json.dump({"starts": starts, "durs": durs, "total": len(out) / SR, "ding": starts[19] - 1.1}, open(TIMING, "w"))
    print("total", len(out) / SR)


if len(sys.argv) > 1 and sys.argv[1] == "mix":
    build_mix(); sys.exit()

T = json.load(open(TIMING))
starts, durs, TOTAL = T["starts"], T["durs"], T["total"]
raw, _ = sf.read(WORK + "dialogue.wav")
hop = SR // FPS
nfr = int(math.ceil(TOTAL * FPS))
env = np.array([np.sqrt(np.mean(raw[k * hop:(k + 1) * hop] ** 2)) if k * hop < len(raw) else 0 for k in range(nfr)])
env = env / (np.percentile(env[env > 0.005], 90) + 1e-9)


def line_at(tt):
    for i in range(N):
        if starts[i] <= tt < starts[i] + durs[i]:
            return i
    return None


def last_line(tt):
    return max([k for k in range(N) if starts[k] <= tt] or [0])


def shot_for(tt):
    i = line_at(tt)
    if i is None:
        p = last_line(tt)
        if p == 18 and tt > T["ding"] - 0.25:
            return "skip_phone"
        return SHOT[p]
    return SHOT[i]


S = 2.0
arts = {k: Image.open(ART + k + ".jpg").convert("RGB").resize((1144, 2048), Image.LANCZOS) for k in MOUTH}
POP = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", 86)
TITLEF = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", 58)
TAGF = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", 40)
EMO = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
emoji = Image.new("RGBA", (140, 140), (0, 0, 0, 0)); ImageDraw.Draw(emoji).text((0, 0), "\U0001F62D", font=EMO, embedded_color=True)
emoji = emoji.crop(emoji.getbbox()).resize((60, 60), Image.LANCZOS)


def skin(shot, x, y):
    return arts[shot].getpixel((int(x), int(y - 18 * S)))


def draw_mouth(img, shot, who, openv):
    if who not in MOUTH[shot]:
        return
    x, y, w = MOUTH[shot][who]
    x, y, w = x * S, y * S, w * S
    d = ImageDraw.Draw(img)
    if who == "skip":
        cw_ = 0.75 if shot == "driveway" else 1.15
        d.ellipse([x - w * cw_, y - w * 0.36, x + w * cw_, y + w * 0.36], fill=skin(shot, x, y))
    h = max(4, w * (0.12 + 0.75 * openv))
    d.ellipse([x - w * 0.55, y - h * 0.5, x + w * 0.55, y + h * 0.5], fill=(70, 10, 18), outline=(0, 0, 0), width=int(3 * S))
    if openv > 0.35:
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


def title(img, tt):
    d = ImageDraw.Draw(img)
    late = tt >= T["ding"] - 0.25
    rows = ["A few minutes later..."] if late else ["When your coworker brings", "a payment plan"]
    bw = max(d.textlength(r, font=TITLEF) for r in rows) + 60 + (0 if late else 80)
    bh = 68 * len(rows) + 36
    bx, by = (W - bw) / 2, 150
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=18, fill=(255, 255, 255), outline=(0, 0, 0), width=4)
    for n, r in enumerate(rows):
        d.text((bx + 30, by + 16 + 68 * n), r, font=TITLEF, fill=(0, 0, 0))
    if not late:
        img.paste(emoji, (int(bx + bw - 88), int(by + bh - 60 - 22)), emoji)
    tag = "SKIP  EP 2"
    tw = d.textlength(tag, font=TAGF)
    d.rounded_rectangle([W - tw - 70, 60, W - 30, 120], radius=14, fill=(255, 122, 26))
    d.text((W - tw - 50, 66), tag, font=TAGF, fill=(255, 255, 255))


def frame(n):
    tt = n / FPS
    shot = shot_for(tt)
    i = line_at(tt)
    li = i if i is not None else last_line(tt)
    p = min(1.0, (tt - starts[li]) / max(1.0, durs[li]))
    z = 1.0 + 0.04 * p + (0.12 if li in PUNCH and p > 0.55 else 0)
    if li == 20:
        z = 1.0 + 0.25 * min(1, (tt - starts[20]) / 0.3)
    z *= 1.0 + 0.004 * math.sin(tt * 2.1)
    fx, fy = FACE[shot]
    fx, fy = fx * S, fy * S
    cw, ch = 1144 / z, 1144 / z * (H / W)
    cx = min(max(fx, cw / 2), 1144 - cw / 2) if z > 1.001 else 572
    cy = min(max(fy + 80, ch / 2), 2048 - ch / 2)
    img = arts[shot].copy()
    if i is not None:
        draw_mouth(img, shot, lines[i]["kind"], float(np.clip(env[n] if n < len(env) else 0, 0, 1)))
    img = img.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.BILINEAR)
    if li == 20 and i is not None:  # shake on the shout
        img = img.transform(img.size, Image.AFFINE, (1, 0, 8 * math.sin(tt * 60), 0, 1, 6 * math.cos(tt * 53)))
    title(img, tt)
    caption(img, tt)
    return img


if __name__ == "__main__":
    a, b = int(sys.argv[1]), int(sys.argv[2])
    if a == -1:
        print(nfr, TOTAL); sys.exit()
    out = sys.stdout.buffer
    for n in range(a, min(b, nfr)):
        out.write(frame(n).tobytes())
