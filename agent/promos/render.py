import sys, os, math, subprocess, numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from promos import PROMOS, PHONE_SPOKEN

W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
POP = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
POPS = "/usr/share/fonts/truetype/google-fonts/Poppins-SemiBold.ttf"
if not os.path.exists(POPS): POPS = POP
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
F = lambda p, s: ImageFont.truetype(p, s)
BG = (10, 12, 26)
COLS = [(59, 155, 255), (155, 123, 255), (45, 212, 160), (255, 92, 147), (255, 178, 63)]
ROLES = ["RESEARCH", "WRITE", "BUILD", "POST", "FOLLOW-UP"]
GRAD = [(77, 163, 255), (168, 120, 255), (255, 92, 147)]

def make_bg():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 60): d.line([(x, 0), (x, H)], fill=(18, 22, 42))
    for y in range(0, H, 60): d.line([(0, y), (W, y)], fill=(18, 22, 42))
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([W/2-330, -200, W/2+330, H+200], fill=110)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    im = Image.composite(Image.new("RGB", (W, H), (70, 40, 130)), im, glow)
    return im
BGIMG = make_bg()

def bot(d, cx, cy, s, col, t=0.0):
    bob = math.sin(t * 3) * 6 * s
    cy += bob
    k = lambda v: v * s
    d.line([(cx, cy - k(150)), (cx, cy - k(110))], fill=col, width=int(k(10)))
    d.ellipse([cx - k(18), cy - k(175), cx + k(18), cy - k(139)], fill=col)
    d.rounded_rectangle([cx - k(110), cy - k(110), cx + k(110), cy + k(60)], radius=int(k(45)), outline=col, width=int(k(16)), fill=(14, 18, 34))
    d.rounded_rectangle([cx - k(78), cy - k(75), cx + k(78), cy + k(20)], radius=int(k(30)), fill=(8, 10, 20))
    blink = (t % 3.2) > 3.05
    for ex in (-38, 38):
        if blink: d.line([(cx + k(ex - 16), cy - k(30)), (cx + k(ex + 16), cy - k(30))], fill=col, width=int(k(8)))
        else: d.ellipse([cx + k(ex - 17), cy - k(52), cx + k(ex + 17), cy - k(10)], fill=col)
    d.arc([cx - k(30), cy - k(25), cx + k(30), cy + k(15)], 20, 160, fill=col, width=int(k(7)))
    d.rounded_rectangle([cx - k(70), cy + k(75), cx + k(70), cy + k(185)], radius=int(k(30)), fill=col)
    d.ellipse([cx - k(12), cy + k(118), cx + k(12), cy + k(142)], fill=(240, 240, 250))
    sw = math.sin(t * 4) * 10
    d.line([(cx - k(70), cy + k(100)), (cx - k(115), cy + k(160 + sw))], fill=col, width=int(k(20)))
    d.line([(cx + k(70), cy + k(100)), (cx + k(115), cy + k(160 - sw))], fill=col, width=int(k(20)))
    d.rounded_rectangle([cx - k(55), cy + k(185), cx - k(15), cy + k(225)], radius=int(k(12)), fill=col)
    d.rounded_rectangle([cx + k(15), cy + k(185), cx + k(55), cy + k(225)], radius=int(k(12)), fill=col)

def grad_text(im, xy, text, font):
    d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), text, font=font)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    mask = Image.new("L", (w + 4, h + 20), 0)
    ImageDraw.Draw(mask).text((-bb[0], -bb[1]), text, font=font, fill=255)
    g = Image.new("RGB", mask.size)
    gd = ImageDraw.Draw(g)
    for x in range(mask.size[0]):
        p = x / max(1, mask.size[0] - 1)
        a, b, q = (GRAD[0], GRAD[1], p * 2) if p < .5 else (GRAD[1], GRAD[2], (p - .5) * 2)
        gd.line([(x, 0), (x, mask.size[1])], fill=tuple(int(a[i] + (b[i] - a[i]) * q) for i in range(3)))
    im.paste(g, (int(xy[0]), int(xy[1])), mask)

def center(d, y, text, font, fill):
    bb = d.textbbox((0, 0), text, font=font)
    d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], y), text, font=font, fill=fill)

def fit(text, path, size, maxw):
    f = F(path, size)
    while f.getlength(text) > maxw and size > 30:
        size -= 4; f = F(path, size)
    return f

def wrap(text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if font.getlength(t) <= maxw: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

def frame(p, t, T, scene_t):
    im = BGIMG.copy()
    d = ImageDraw.Draw(im)
    s1, s2 = scene_t
    tag = F(MONO, 34)
    if t < s1:  # hook
        center(d, 150, "AUTONOMOUS AI AGENTS", tag, (45, 212, 160))
        for i, line in enumerate(p["hook"]):
            f = fit(line, POP, 96, W - 120)
            y = 300 + i * 125
            if i == p["hl"]:
                bb = d.textbbox((0, 0), line, font=f)
                grad_text(im, ((W - (bb[2] - bb[0])) / 2, y), line, f)
            else:
                center(d, y, line, f, (245, 245, 255))
        b = p["bot"] if p["bot"] >= 0 else 0
        bot(d, W / 2, 1050, 1.5, COLS[b], t)
    elif t < s2:  # agent at work
        if p["bot"] >= 0:
            b = p["bot"]
            center(d, 150, f"AGENT {b+1:02d} / 05", tag, COLS[b])
            bot(d, W / 2, 620, 1.55, COLS[b], t)
            center(d, 1010, ROLES[b], F(MONO, 72), COLS[b])
        else:
            center(d, 150, "THE CREW", tag, (45, 212, 160))
            for i in range(5):
                bot(d, 140 + i * 200, 700, .62, COLS[i], t + i)
                center_x = 140 + i * 200
                f = F(MONO, 26); bb = d.textbbox((0, 0), ROLES[i], font=f)
                d.text((center_x - (bb[2] - bb[0]) / 2, 880), ROLES[i], font=f, fill=COLS[i])
        col = COLS[p["bot"]] if p["bot"] >= 0 else COLS[2]
        d.rounded_rectangle([90, 1120, W - 90, 1420], radius=26, outline=col, width=4, fill=(12, 15, 30))
        n = int(len(p["task"]) * min(1, (t - s1) / max(.5, (s2 - s1) * .8)))
        mf = F(MONO, 40)
        lines = wrap(p["task"][:n], mf, W - 260)
        for i, ln in enumerate(lines[:4]):
            d.text((130, 1160 + i * 58), ln, font=mf, fill=(220, 225, 240))
        if int(t * 2) % 2 == 0:
            last = lines[-1] if lines else ""
            x = 130 + mf.getlength(last) + 6
            y = 1160 + (max(1, len(lines)) - 1) * 58
            d.rectangle([x, y + 6, x + 22, y + 50], fill=(45, 212, 160))
    else:  # end card
        center(d, 150, "NOW BUILDING FOR SMALL BUSINESSES", tag, (45, 212, 160))
        center(d, 330, "I've Got An Agent", F(POP, 92), (245, 245, 255))
        f = F(POP, 92); bb = d.textbbox((0, 0), "That Can Do That.", font=f)
        grad_text(im, ((W - (bb[2] - bb[0])) / 2, 455), "That Can Do That.", f)
        for i in range(5):
            bot(d, 140 + i * 200, 860, .6, COLS[i], t + i)
        center(d, 1130, "Call or text", F(POPS, 60), (200, 205, 225))
        pill = [110, 1230, W - 110, 1400]
        d.rounded_rectangle(pill, radius=85, fill=(110, 120, 255))
        center(d, 1262, "(252) 543-9014", F(POP, 92), (255, 255, 255))
    # spoken-word captions along the bottom (most people watch muted)
    cap = None
    for (a, b, txt) in p.get("_caps", []):
        if a <= t < b: cap = txt
    if cap:
        cf = F(POPS, 52)
        for i, ln in enumerate(wrap(cap, cf, W - 160)[:3]):
            center(d, 1560 + i * 70, ln, cf, (245, 245, 255))
    return im

def chunks(text, start, dur):
    import re
    parts = [x.strip() for x in re.split(r'(?<=[.?!,:])\s+', text) if x.strip()]
    out, cur = [], ""
    for x in parts:
        if len((cur + " " + x).split()) <= 9: cur = (cur + " " + x).strip()
        else:
            if cur: out.append(cur)
            cur = x
    if cur: out.append(cur)
    tot = sum(len(c) for c in out); res = []; t0 = start
    for c in out:
        d_ = dur * len(c) / tot; res.append((t0, t0 + d_, c)); t0 += d_
    return res

def tts(k, text, path):
    s, sr = k.create(text, voice="am_onyx", speed=1.0, lang="en-us")
    sf.write(path, s, sr)
    return len(s) / sr, sr

if __name__ == "__main__":
    from kokoro_onnx import Kokoro
    k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
    only = sys.argv[2:]
    for p in PROMOS:
        if only and p["id"] not in only: continue
        a1, sr = tts(k, p["vo"], f"/tmp/{p['id']}_a.wav")
        a2, _ = tts(k, "I've got an agent that can do that. " + PHONE_SPOKEN, f"/tmp/{p['id']}_b.wav")
        x1, _ = sf.read(f"/tmp/{p['id']}_a.wav"); x2, _ = sf.read(f"/tmp/{p['id']}_b.wav")
        pad = lambda sec: np.zeros(int(sr * sec))
        if p["id"] == "14-crew":  # VO already ends with the tagline
            x2, _ = sf.read(f"/tmp/{p['id']}_b.wav")
            tts(k, PHONE_SPOKEN, f"/tmp/{p['id']}_b.wav"); x2, _ = sf.read(f"/tmp/{p['id']}_b.wav")
        audio = np.concatenate([pad(.4), x1, pad(.5), x2, pad(.9)])
        T = len(audio) / sr
        s1 = .4 + min(3.2, a1 * .35)
        s2 = .4 + len(x1) / sr + .3
        tag2 = "Call or text (252) 543-9014." if p["id"] == "14-crew" else "I've got an agent that can do that. Call or text (252) 543-9014."
        p["_caps"] = chunks(p.get("vo_cap", p["vo"]), .4, len(x1) / sr) + chunks(tag2, .4 + len(x1) / sr + .5, len(x2) / sr)
        sf.write(f"/tmp/{p['id']}.wav", audio, sr)
        out = os.path.join(OUT, f"agent-{p['id']}.mp4")
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", f"/tmp/{p['id']}.wav", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(int(T * FPS)):
            pr.stdin.write(frame(p, i / FPS, T, (s1, s2)).tobytes())
        pr.stdin.close(); pr.wait()
        print(p["id"], round(T, 1), "s", out, flush=True)
