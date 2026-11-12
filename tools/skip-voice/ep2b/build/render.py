"""Skip Ep 1 puppet render: Evan-style stills, mouth flap from the voice envelope, push-ins, word-by-word captions, title bar.
Writes raw RGB frames to stdout for ffmpeg."""
import json, sys, math, subprocess
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
ART = "/home/claude/ep2/art/"
NL = 40
GAP = {12: 0.9, 13: 0.5, 28: 0.6, 34: 0.7, 35: 0.9, 39: 0.8}
lines = json.load(open("/home/claude/morning-word-videos._/tools/skip-voice/ep2b/lines.json"))
# caption text = real spelling (voice text has 'red' for 'read')
CAP = {33: "You remember. You lost your wallet. Thursday.", 30: "No. Not Friday. Last Friday you paid me $40.", 32: "Hold up. Where did that $40 come from?", 39: "Technically, I paid you back. You're welcome.", 22: "Mid?! So you ate it, and then you gave it a review?", 24: "Two stars?! My mama been making that pudding since 1994!", 37: "Nah. I gave it back. Minus $40."}

# ---- timing: rebuild the same stitch as the dialogue track
sr = 44100
starts, durs, env_parts = [], [], []
t = 0.0
gap = GAP
for i in range(NL):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"/home/claude/ep2/final2/u{i:03d}.wav", "-ar", "44100", "-ac", "1", f"/tmp/r{__import__('os').getpid()}.wav"], check=True)
    a, _ = sf.read(f"/tmp/r{__import__('os').getpid()}.wav")
    nz = np.where(np.abs(a) > 0.01)[0]
    a = a[max(0, nz[0] - 400):nz[-1] + 2000]
    starts.append(t); durs.append(len(a) / sr)
    t += len(a) / sr + gap.get(i, 0.28)
TOTAL = t
raw, _ = sf.read("/home/claude/ep2/dialogue_raw.wav")
hop = sr // FPS
nfr = int(math.ceil(TOTAL * FPS))
env = np.array([np.sqrt(np.mean(raw[k * hop:(k + 1) * hop] ** 2)) if k * hop < len(raw) else 0 for k in range(nfr)])
env = env / (np.percentile(env[env > 0.005], 90) + 1e-9)

def line_at(tt):
    for i in range(NL):
        if starts[i] <= tt < starts[i] + durs[i]:
            return i
    return None

# ---- shots: (art, speaker-mouth map). Skip on route, Dre on couch, Friday driveway for 17-18
MOUTH = {"breakroom": {"skip": (165, 445, 26), "dre": (445, 505, 20)}, "dre_table": {"dre": (295, 532, 44)}, "skip_fridge": {"skip": (332, 505, 70)}}
FACE = {"breakroom": (300, 470), "dre_table": (290, 470), "skip_fridge": (330, 460)}
SKIN = {"breakroom": (250, 250, 250), "dre_table": (255, 255, 255), "skip_fridge": (252, 252, 252)}
WIDE = {0, 1, 2, 3, 4, 5, 11, 15, 16, 17, 39}
def shot_for(tt):
    i = line_at(tt)
    if i is None:
        prev = max([k for k in range(NL) if starts[k] <= tt] or [0])
        i = prev
    if i in WIDE:
        return "breakroom"
    return "dre_table" if lines[i]["kind"] == "dre" else "skip_fridge"

arts = {}
for k in MOUTH:
    im = Image.open(ART + k + ".jpg").convert("RGB")
    arts[k] = im.resize((1144, 2048), Image.LANCZOS)  # x2
S = 2.0

POP = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", 86)
TITLEF = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", 60)
EMO = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
emoji = Image.new("RGBA", (140, 140), (0, 0, 0, 0)); ImageDraw.Draw(emoji).text((0, 0), "\U0001F62D", font=EMO, embedded_color=True)
emoji = emoji.crop(emoji.getbbox()).resize((62, 62), Image.LANCZOS)

def draw_mouth(img, shot, who, openv):
    if shot not in MOUTH or who not in MOUTH[shot]:
        return
    x, y, w = MOUTH[shot][who]
    x, y, w = x * S, y * S, w * S
    d = ImageDraw.Draw(img)
    if who == "skip":  # cover the drawn mouth with skin
        d.ellipse([x - w * 0.75, y - w * 0.32, x + w * 0.75, y + w * 0.32], fill=SKIN[shot])
    h = max(4, w * (0.12 + 0.75 * openv))
    d.ellipse([x - w * 0.55, y - h * 0.5, x + w * 0.55, y + h * 0.5], fill=(70, 10, 18), outline=(0, 0, 0), width=int(3 * S))
    if openv > 0.35:  # tongue
        d.chord([x - w * 0.32, y, x + w * 0.32, y + h * 0.48], 180, 360, fill=(220, 90, 100))
        d.chord([x - w * 0.32, y + h * 0.05, x + w * 0.32, y + h * 0.48], 0, 180, fill=(220, 90, 100))

def words_for(i):
    return CAP.get(i, lines[i]["text"]).split()

def caption(img, tt):
    i = line_at(tt)
    if i is None:
        return
    ws = words_for(i)
    wt = np.cumsum([len(w) + 2 for w in ws]); wt = wt / wt[-1] * durs[i]
    k = int(np.searchsorted(wt, tt - starts[i]))
    k = min(k, len(ws) - 1)
    # show a chunk of up to 3 words ending at the current word
    a0 = (k // 3) * 3
    chunk = ws[a0:a0 + 3]
    d = ImageDraw.Draw(img)
    txt = " ".join(chunk).upper()
    while d.textlength(txt, font=POP) > W - 80 and len(chunk) > 1:
        chunk = chunk[:-1]; txt = " ".join(chunk).upper()
    tw = d.textlength(txt, font=POP)
    x0, y0 = (W - tw) / 2, 1320
    # highlight current word yellow
    xx = x0
    for j, w in enumerate(chunk):
        wd = w.upper() + (" " if j < len(chunk) - 1 else "")
        col = (255, 225, 40) if a0 + j == k else (255, 255, 255)
        d.text((xx, y0), wd, font=POP, fill=col, stroke_width=9, stroke_fill=(0, 0, 0))
        xx += d.textlength(wd, font=POP)

def title(img, tt):
    d = ImageDraw.Draw(img)
    lines_ = ["When your coworker", "eats your lunch"]
    bh = 70 * len(lines_) + 40
    by = 150
    bw = max(d.textlength(l, font=TITLEF) for l in lines_) + 60 + 80
    bx = (W - bw) / 2
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=18, fill=(255, 255, 255), outline=(0, 0, 0), width=4)
    for n, l in enumerate(lines_):
        d.text((bx + 30, by + 18 + 70 * n), l, font=TITLEF, fill=(0, 0, 0))
    img.paste(emoji, (int(bx + bw - 90), int(by + bh - 62 - 22)), emoji)

def frame(n):
    tt = n / FPS
    shot = shot_for(tt)
    # shot start for push-in
    base = arts[shot]
    i = line_at(tt)
    # slow push-in within each line, punch on caps-lines
    li = i if i is not None else max([k for k in range(NL) if starts[k] <= tt] or [0])
    p = min(1.0, (tt - starts[li]) / max(1.0, durs[li]))
    punch = li in (6, 12, 14, 20, 22, 24, 26, 37, 38)
    z = 1.0 + 0.04 * p + (0.12 if punch and p > 0.55 else 0)
    z *= 1.0 + 0.004 * math.sin(tt * 2.1)
    fx, fy = FACE[shot]
    fx, fy = fx * S, fy * S
    cw, ch = 1144 / z, 1144 / z * (H / W)
    cx = min(max(fx, cw / 2), 1144 - cw / 2) if z > 1.001 else 572
    cy = min(max(fy + 80, ch / 2), 2048 - ch / 2)
    img = base.copy()
    who = lines[i]["kind"] if i is not None else None
    if who:
        draw_mouth(img, shot, who, float(np.clip(env[n] if n < len(env) else 0, 0, 1)))
    img = img.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.BILINEAR)
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
