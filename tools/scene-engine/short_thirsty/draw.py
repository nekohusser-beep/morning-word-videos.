#!/usr/bin/env python3
"""The Thirsty Loop, vertical 9:16 Short. Frame-by-frame colored stick-figure animation from anim_stick's rig.
Design space 1080x1920 (u=1). Ground line 1500. Captions sit below the ground (MarginV 205 of 1280 -> ~y1610).
  draw.py voices SCENES ASSETS [--voice am_michael --speed 1.0]
  draw.py render SCENES ASSETS [--fps 12]
"""
import argparse, json, math, os, sys, subprocess, tempfile, shutil
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import anim_stick as S
from anim_stick import (P, fig, walk, pose_at, ease, rad, cup, plate, stack, clock, phone, qmark, note, check, cross, bubble, spiral,
                        hills, sunrise, ell, INK, GOLD, GOLDL, SKY, WALL, FLOOR, TEAL, PINK, PURP, YEL, GRN, BLUE, RED, ORANGE, CREAM, RAIN)
from draw_stick import Canvas, S as SS
from PIL import ImageFont, ImageDraw

W, H = 1080, 1920
G = 1500           # ground / floor line
K = 1.9            # figure scale
HIP = G - 176 * K  # standing hip height
SEAT = G - 88 * K  # sitting hip height (shin length)
HEAD, TAIL = 0.15, 0.35


class VCanvas(Canvas):
    """1080x1920 design space mapped 1:1 (Canvas assumes 1080-high design; override the scale)."""
    def __init__(s, w, h, bg, seed):
        super().__init__(w, h, bg=bg, seed=seed); s.u = 1.0; s.lw = 9 * SS


def stand(hx, **kw): return P(hx=hx, hy=HIP, **kw)
def sit(hx=400, **kw): return P(hx=hx, hy=SEAT, ll1=88, ll2=2, rl1=82, rl2=2, **kw)


def F(c, Z, **kw): return fig(c, Z, k=K, **kw)


# ---------------------------------------------------------------- rooms (vertical)
def room(c, wall=WALL, floor=FLOOR, window=True):
    c.rect(0, 0, W, H, fill=wall, outline=False); c.rect(0, G, W, H, fill=floor, outline=False); c.line([(0, G), (W, G)])
    if window:
        c.rect(640, 520, 1000, 900, fill=SKY); c.line([(820, 520), (820, 900)]); c.line([(640, 710), (1000, 710)])


def sofa(c, x=60):
    c.rect(x + 40, SEAT - 190, x + 640, SEAT - 30, fill=PURP)
    c.rect(x, SEAT - 40, x + 680, G, fill=(130, 90, 215)); c.rect(x, SEAT - 50, x + 80, G, fill=(110, 76, 190)); c.rect(x + 600, SEAT - 50, x + 680, G, fill=(110, 76, 190))
    c.rect(x + 80, SEAT + 10, x + 600, SEAT + 40, fill=(180, 150, 245), outline=False)


def kitchen(c):
    c.rect(0, 0, W, H, fill=TEAL, outline=False); c.rect(0, G, W, H, fill=(236, 214, 178), outline=False); c.line([(0, G), (W, G)])
    c.rect(560, G - 260, W, G, fill=(205, 160, 112)); c.rect(560, G - 290, W, G - 255, fill=(245, 238, 225))  # counter


def cabinet(c, open_=0.0):
    c.rect(560, 420, 1040, 820, fill=(246, 244, 236)); c.line([(800, 420), (800, 820)])
    c.rect(560, 420, 800, 820, fill=(70, 62, 66)); c.line([(560, 620), (800, 620)], (110, 100, 104), 1.0)
    wd = 240 * (1 - open_ * .85); c.poly([(560, 420), (560 + wd, 430), (560 + wd, 810), (560, 820)], (255, 255, 250))


def sink(c):
    c.rect(620, G - 320, 1020, G - 255, fill=(120, 170, 215)); c.line([(1040, G - 290), (1040, G - 450), (960, G - 470)], INK, 1.6)


def title(c, text, x, y, size=96, col=INK, bg=YEL, rot=-3):
    """Hand-lettered sticky note title (Poppins Bold), used for the hook."""
    f = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", int(size * SS))
    d = ImageDraw.Draw(c.im, "RGBA"); tw = d.textlength(text, font=f) / SS
    pad = 28; c.poly([(x - tw / 2 - pad, y - size * .75), (x + tw / 2 + pad, y - size * .75), (x + tw / 2 + pad, y + size * .55), (x - tw / 2 - pad, y + size * .55)], bg)
    d.text(((x - tw / 2) * SS, (y - size * .72) * SS), text, font=f, fill=col + (255,))


# ---------------------------------------------------------------- scenes
def s01(c, p, t, T):  # couch, thirsty, bubble cup
    room(c); sofa(c)
    keys = [(0, sit(ra1=75, ra2=160, la1=20, la2=40, mood="flat")), (.25, sit(ra1=80, ra2=165, mood="worry")), (.6, sit(lean=12, ra1=30, ra2=40, mood="open")), (1, sit(lean=14, ra1=30, ra2=40, mood="open"))]
    Z = pose_at(keys, p); f = F(c, Z)
    s = ease((p - .12) / .1); bubble(c, 700, 1000, s * 1.2, tail_from=f["head"])
    if s > .05: cup(c, 700, 1060 + 8 * math.sin(t * 3), 1.8 * s, level=.8)
    title(c, "POV: my brain", 540, 260, 92)
    title(c, "just wants water", 540, 400, 72, bg=(255, 255, 255), rot=2)


def s02(c, p, t, T):  # walk in, open cabinet
    kitchen(c); cabinet(c, ease((p - .7) / .15))
    keys = [(0, stand(120, mood="flat")), (.6, stand(420, mood="flat", lean=4)), (.72, stand(440, mood="flat", ra1=-70, ra2=-120)), (1, stand(440, mood="flat", ra1=-70, ra2=-120))]
    Z = pose_at(keys, p)
    if p < .62: Z = walk(Z, t, 1.0, 10)
    F(c, Z)


def s03(c, p, t, T):  # empty cabinet, bubble X
    kitchen(c); cabinet(c, 1.0)
    keys = [(0, stand(440, mood="worry", ra1=-70, ra2=-120)), (.4, stand(440, mood="worry", ra1=150, ra2=200, tilt=6)), (1, stand(440, mood="flat", ra1=20, ra2=30, tilt=0))]
    f = F(c, pose_at(keys, p))
    s = ease((p - .1) / .1) * (1 - ease((p - .7) / .12)); bubble(c, 330, 560, s * 1.2, tail_from=f["head"])
    if s > .05: cup(c, 330, 620, 1.7 * s); cross(c, 330, 560, 1.6 * s)


def s04(c, p, t, T):  # the sink tower (no figure)
    kitchen(c); sink(c)
    n = min(12, 3 + int(p * 14)); stack(c, 820, G - 330, n, .4 + p * 1.5, t)


def s05(c, p, t, T):  # calendar X bubble + scrubbing
    kitchen(c); sink(c); stack(c, 820, G - 330, 11, .3, t)
    Z = stand(380, mood="worry" if p < .5 else "tired", lean=8); Z["ra1"] = 70 + 24 * math.sin(t * 13); Z["ra2"] = 100 + 24 * math.sin(t * 13)
    f = F(c, Z); plate(c, f["rh"][0] + 60, f["rh"][1], .7, CREAM)
    s = ease((p - .05) / .1) * (1 - ease((p - .55) / .12)); bubble(c, 300, 560, s * 1.2, tail_from=f["head"])
    if s > .05:
        c.rect(300 - 90 * s, 500 - 80 * s, 300 + 90 * s, 640, fill=(255, 255, 255)); c.rect(300 - 90 * s, 500 - 80 * s, 300 + 90 * s, 500 - 30 * s, fill=RED); cross(c, 300, 580, 1.4 * s)


def s06(c, p, t, T):  # phone buzzes, looks around
    kitchen(c); sink(c); stack(c, 820, G - 330, 9, .2, t)
    Z = stand(380, mood="open", look=math.sin(t * 6) * 1.3, tilt=math.sin(t * 6) * 9, ra1=10, ra2=20)
    Z["ra1"], Z["ra2"] = (60 + 10 * math.sin(t * 9), 120) if p < .2 else (10, 20)
    f = F(c, Z)
    for i in range(3):
        s = ease((p - .25 - i * .18) / .1) * (1 - ease((p - .6 - i * .18) / .1))
        if s > .05: qmark(c, 250 + i * 130, 720 - i * 60, 1.4 * s, RAIN[i * 2])
    bz = .05 * math.sin(t * 40) * (p < .3); phone(c, f["rh"][0] + 10, f["rh"][1] - 60 + bz * 100, 1.1)


def s07(c, p, t, T):  # it's in my hand
    kitchen(c); sink(c); stack(c, 820, G - 330, 9, .2, t)
    keys = [(0, stand(380, mood="open", ra1=10, ra2=20)), (.3, stand(380, mood="open", ra1=70, ra2=150, tilt=8)), (.55, stand(380, mood="tired", ra1=70, ra2=150, tilt=8)), (1, stand(380, mood="tired", ra1=70, ra2=150, tilt=10))]
    f = F(c, pose_at(keys, p)); phone(c, f["rh"][0] + 10, f["rh"][1] - 60, 1.1)
    s = ease((p - .5) / .12)
    if s > .05: title(c, "...", f["head"][0] + 160, f["head"][1] - 120, int(90 * s), bg=(255, 255, 255))


def s08(c, p, t, T):  # abstract: one hour later
    c.rect(0, 0, W, H, fill=(50, 34, 100), outline=False)
    spiral(c, 540, 900, 440, 4.5, t * 1.4, 2.2)
    clock(c, 540, 900, 230, t * 560, t * 47)
    for i, kind in enumerate(("phone", "plate", "cup", "x")):
        a = t * 1.1 + i * math.pi / 2; x, y = 540 + 380 * math.cos(a), 900 + 520 * math.sin(a)
        if kind == "phone": phone(c, x, y, .9)
        elif kind == "plate": plate(c, x, y, 1.0, CREAM)
        elif kind == "cup": cup(c, x, y + 30, 1.0)
        else: qmark(c, x, y - 10, 1.0, YEL)
    title(c, "1 hour later", 540, 300, 96, col=(255, 255, 255), bg=RED)


def s09(c, p, t, T):  # headphones, one song
    room(c, wall=(214, 190, 255), floor=(150, 110, 200), window=False)
    beat = abs(math.sin(t * math.pi * 2.2)); w = math.sin(t * 9)
    Z = P(hx=540, hy=HIP + 14 * beat, mood="smile", tilt=8 * math.sin(t * math.pi * 2.2), ra1=40 + 30 * w, ra2=70 + 30 * w, la1=-40 - 30 * w, la2=-20,
          rl1=6 * w, rl2=6 * w, ll1=-6 * w, ll2=-6 * w)
    F(c, Z, headphones=True)
    for i in range(8):
        u = ((t * .3 + i / 8) % 1); x = 140 + i * 115 + 40 * math.sin(u * 8 + i); y = 1300 - u * 1100
        note(c, x, y, RAIN[(i + 2) % 7], 1.1 + .2 * math.sin(i))
    s = ease((p - .6) / .12)
    if s > .05: title(c, "ONE song", 540, 300, int(100 * s), bg=PINK)


def s10(c, p, t, T):  # wash one cup, check
    kitchen(c); sink(c); stack(c, 820, G - 330, 8, .15, t)
    Z = stand(380, mood="smile", lean=6); Z["ra1"] = 70 + 18 * math.sin(t * 11); Z["ra2"] = 100 + 18 * math.sin(t * 11)
    f = F(c, Z); cup(c, f["rh"][0] + 50, f["rh"][1] + 20, 1.2, level=ease((p - .3) / .4))
    s = ease((p - .7) / .1)
    if s > .05: check(c, 300, 560, 1.6 * s); title(c, "ONE cup", 540, 300, int(100 * s), bg=GRN)


def s11(c, p, t, T):  # calm on couch, bubble floats away
    room(c, wall=(255, 236, 190)); sofa(c)
    f = F(c, sit(lean=-4, mood="smile", ra1=20, ra2=30, la1=10, la2=20))
    u = ease(p * 1.1); x = 420 + 200 * u; y = 900 - 900 * u; s = max(.05, 1.2 - 1.0 * u)
    bubble(c, x, y, s, tail_from=f["head"] if p < .3 else None); spiral(c, x, y, 110 * s, 3.0, t * 1.6, 1.3)
    c.glow(820, 710, 300 + 160 * ease(p), col=GOLD, strength=190)


def sunrise_v(c, q, t, p):
    for i in range(40):
        u = i / 39; col = (int(70 + 185 * u), int(60 + 120 * u), int(150 - 20 * u) if u < .5 else int(110 + 20 * u))
        c.rect(0, i * 48, W, i * 48 + 50, fill=col, outline=False)
    sy = 1500 - 700 * ease(q); c.glow(540, sy, 520, col=GOLDL, strength=230)
    c.rays(540, sy, 170, 560, 26, 180 + 8 * math.sin(t), 360 - 8 * math.sin(t), YEL); c.circ(540, sy, 150, fill=YEL, w=1.2)
    for i in range(3):
        x = (150 + i * 420 + t * 25 * (i + 1)) % 1400 - 160; y = 300 + 110 * i
        for dx, dy, r in ((-50, 0, 46), (0, -18, 56), (56, 4, 44)): c.circ(x + dx, y + dy, r, fill=(255, 255, 255), outline=False)
    for j, col in enumerate([(110, 170, 130), (80, 150, 120), (50, 120, 110)]):
        pts = [(0, H)] + [(x, 1250 + j * 170 + 70 * math.sin(x / 260 + j * 1.7) + 25 * math.sin(x / 110 + j)) for x in range(0, W + 1, 60)] + [(W, H)]
        c.poly(pts, col)
    title(c, "Isaiah 26:3", 540, 240, 88, bg=(255, 255, 255))


def s12(c, p, t, T): sunrise_v(c, .6 * p, t, p)
def s12b(c, p, t, T): sunrise_v(c, .6 + .4 * p, t, p)


def s13(c, p, t, T):  # loop back: couch, full cup, peace
    room(c); sofa(c)
    f = F(c, sit(lean=-2, mood="smile", ra1=40, ra2=80, la1=10, la2=20))
    cup(c, f["rh"][0] + 10, f["rh"][1] + 30, 1.5, level=.85)
    c.glow(820, 710, 320, col=GOLD, strength=170)
    s = ease((p - .45) / .12)
    if s > .05: title(c, "One thing at a time.", 540, 300, int(78 * s), bg=(255, 255, 255)); title(c, "That's the whole trick.", 540, 430, int(78 * s), bg=YEL)


RECIPES = {f"s{i:03d}": fn for i, fn in enumerate((s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s13), 1)}


def draw_frame(args):
    fn, p, t, T, seed, path = args
    c = VCanvas(W, H, bg=(255, 255, 255), seed=seed); fn(c, p, t, T); c.save(path)


def wav_len(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip())


def cmd_voices(a):
    from kokoro_onnx import Kokoro
    import soundfile as sf
    d = os.environ.get("KOKORO_DIR", "."); Kk = Kokoro(os.path.join(d, "kokoro-v1.0.onnx"), os.path.join(d, "voices-v1.0.bin"))
    os.makedirs(os.path.join(a.assets, "vo"), exist_ok=True)
    for s in json.load(open(a.scenes))["scenes"]:
        au, sr = Kk.create(s["vo"], voice=a.voice, speed=a.speed, lang="en-us"); sf.write(os.path.join(a.assets, "vo", f"{s['id']}.wav"), au, sr); print(s["id"], f"{len(au) / sr:.1f}s")


def cmd_render(a):
    tmp = tempfile.mkdtemp(prefix="short_")
    try:
        for s in json.load(open(a.scenes))["scenes"]:
            if a.only and s["id"] not in a.only: continue
            i = s["id"]; fn = RECIPES[i]; vo = os.path.join(a.assets, "vo", f"{i}.wav")
            T = (wav_len(vo) if os.path.exists(vo) else s["est_sec"]) + HEAD + TAIL
            n = int(math.ceil(T * a.fps)); d = os.path.join(tmp, i); os.makedirs(d)
            jobs = [(fn, k / max(1, n - 1), k / a.fps, T, (k % 3) + 1, os.path.join(d, f"f{k:04d}.png")) for k in range(n)]
            with Pool() as pool: pool.map(draw_frame, jobs, chunksize=4)
            out = os.path.join(a.assets, f"{i}.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", os.path.join(d, "f%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
            shutil.rmtree(d); print(i, f"{n} frames, {T:.1f}s", flush=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("voices"); v.add_argument("scenes"); v.add_argument("assets"); v.add_argument("--voice", default="am_michael"); v.add_argument("--speed", type=float, default=1.0)
    r = sub.add_parser("render"); r.add_argument("scenes"); r.add_argument("assets"); r.add_argument("--fps", type=int, default=12); r.add_argument("--only", nargs="*")
    a = ap.parse_args(); (cmd_voices if a.cmd == "voices" else cmd_render)(a)
