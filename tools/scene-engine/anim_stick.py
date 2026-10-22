#!/usr/bin/env python3
"""Frame-by-frame stick-figure animation in code (the old hand-drawn-cartoon method, free, no image tool).
Every frame is drawn fresh from a jointed stick-figure rig, with a little line 'boil' so it reads hand-drawn,
in bright color. Frames are drawn 'on twos' at 12 fps; build.py then picks the clips up as s001.mp4 ... and
cuts them to the voice (hard cuts, voice = skeleton).

  anim_stick.py voices SCENES ASSETS [--voice am_michael --speed 0.95]   # Kokoro voice per scene -> ASSETS/vo/sNNN.wav
  anim_stick.py render SCENES ASSETS [--recipes thirsty --fps 12]        # animated clip per scene -> ASSETS/sNNN.mp4
  (then)  build.py SCENES ASSETS OUT --voice am_michael --speed 0.95

Each scene's clip length = its voice length + build.py HEAD/TAIL pad, so the picture always covers the voice."""
import argparse, json, math, os, subprocess, sys, tempfile, shutil
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw_stick import Canvas, INK, GOLD, GOLDL

W, H = 1280, 720
HEAD, TAIL = 0.15, 0.35  # must match build.py
FACE = (255, 248, 236)
SKY = (120, 200, 255); WALL = (255, 226, 170); FLOOR = (214, 150, 102); SHIRT = (235, 86, 86); PANTS = (60, 100, 200)
TEAL = (150, 222, 210); PINK = (255, 120, 170); PURP = (160, 120, 235); YEL = (255, 206, 60); GRN = (80, 196, 110)
BLUE = (70, 160, 255); RED = (230, 60, 60); ORANGE = (255, 150, 60); CREAM = (240, 236, 224)
RAIN = [RED, ORANGE, YEL, GRN, BLUE, PURP, PINK]
GROUND = 880
K = 1.35  # figure scale


def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def rad(a): return math.radians(a)


# ---------------------------------------------------------------- the rig
BASE = dict(hx=960, hy=GROUND - 176 * K, lean=0, la1=10, la2=16, ra1=-10, ra2=-16, ll1=0, ll2=0, rl1=0, rl2=0, tilt=0, look=0, mood="flat")


def P(**kw): d = dict(BASE); d.update(kw); return d


def sit(hx=470, **kw): return P(hx=hx, hy=745, ll1=88, ll2=2, rl1=82, rl2=2, **kw)


def stand(hx, **kw): return P(hx=hx, **kw)


def pose_at(keys, p):
    if p <= keys[0][0]: return dict(keys[0][1])
    for (p0, a), (p1, b) in zip(keys, keys[1:]):
        if p <= p1:
            u = ease((p - p0) / max(1e-6, p1 - p0)); out = {}
            for k in a:
                out[k] = (a[k] if u < .5 else b[k]) if k == "mood" else a[k] + (b[k] - a[k]) * u
            return out
    return dict(keys[-1][1])


def walk(pz, t, amt=1.0, speed=9.0):
    s = math.sin(t * speed)
    q = dict(pz)
    q["ll1"] += 30 * s * amt; q["ll2"] = q["ll1"] - 20 * max(0, -s) * amt
    q["rl1"] += -30 * s * amt; q["rl2"] = q["rl1"] - 20 * max(0, s) * amt
    q["la1"] += -26 * s * amt; q["la2"] = q["la1"] + 14
    q["ra1"] += 26 * s * amt; q["ra2"] = q["ra1"] + 14
    q["hy"] -= 7 * abs(s) * amt
    return q


def pt(o, a, L, face): return (o[0] + face * L * math.sin(rad(a)), o[1] + L * math.cos(rad(a)))


def fig(c, Z, face=1, shirt=SHIRT, pants=PANTS, k=K, headphones=False):
    """Draw a stick figure from pose Z. Returns {'rh','lh','head'} so props can follow the hands."""
    hip = (Z["hx"], Z["hy"]); lean = Z["lean"]
    TL, UA, FA, TH, SH = 130 * k, 68 * k, 60 * k, 88 * k, 88 * k
    ax = (face * math.sin(rad(lean)), -math.cos(rad(lean)))
    sh = (hip[0] + ax[0] * TL, hip[1] + ax[1] * TL)

    def limb(o, a1, a2, L1, L2, col=None, w=1.0):
        m = pt(o, a1, L1, face); e = pt(m, a2, L2, face)
        if col: c.line([o, m, e], INK, w + .8); c.line([o, m, e], col, w)
        else: c.line([o, m, e], INK, w)
        return e

    lh = limb(sh, Z["la1"], Z["la2"], UA, FA)                                  # back arm
    lf = limb(hip, Z["ll1"], Z["ll2"], TH, SH, pants, 1.5)                     # back leg
    rf = limb(hip, Z["rl1"], Z["rl2"], TH, SH, pants, 1.5)                     # front leg
    for f in (lf, rf): c.line([f, (f[0] + face * 26 * k, f[1])], INK, 1.5)
    perp = (-ax[1], ax[0])
    c.poly([(sh[0] + perp[0] * 25 * k, sh[1] + perp[1] * 25 * k), (sh[0] - perp[0] * 25 * k, sh[1] - perp[1] * 25 * k),
            (hip[0] - perp[0] * 19 * k, hip[1] - perp[1] * 19 * k), (hip[0] + perp[0] * 19 * k, hip[1] + perp[1] * 19 * k)], shirt)
    hr = 38 * k; hc = (sh[0] + ax[0] * (hr + 7 * k) + face * Z["tilt"], sh[1] + ax[1] * (hr + 7 * k))
    c.circ(hc[0], hc[1], hr, fill=FACE)
    if headphones:
        pts = [(hc[0] + (hr + 9) * math.cos(rad(a)), hc[1] + (hr + 9) * math.sin(rad(a))) for a in range(190, 351, 10)]
        c.line(pts, PINK, 1.6)
        for sx in (-1, 1): c.circ(hc[0] + sx * (hr + 7), hc[1] + 4, 14 * k, fill=PINK)
    m = Z["mood"]; lk = Z["look"] * 5
    ey = hc[1] - 6 * k
    for sx in (-1, 1):
        ex = hc[0] + sx * 14 * k
        if m == "tired": c.line([(ex - 7, ey), (ex + 7, ey)], INK, .8)
        else: c.circ(ex + lk, ey, 4.5 * k, fill=INK, outline=False)
        if m == "worry": c.line([(ex - 8, ey - 14 - sx * 3), (ex + 8, ey - 14 + sx * 3)], INK, .7)
    my = hc[1] + 17 * k
    if m == "smile": c.line([(hc[0] - 14 + i * 28 / 8, my - 3 + 9 * math.sin(math.pi * i / 8)) for i in range(9)], INK, .9)
    elif m == "open": c.circ(hc[0], my + 2, 8 * k, fill=INK)
    elif m == "worry": c.line([(hc[0] - 12 + i * 24 / 8, my + 6 - 8 * math.sin(math.pi * i / 8)) for i in range(9)], INK, .9)
    else: c.line([(hc[0] - 10, my), (hc[0] + 10, my)], INK, .9)
    rh = limb(sh, Z["ra1"], Z["ra2"], UA, FA)                                  # front arm
    return {"rh": rh, "lh": lh, "head": hc}


# ---------------------------------------------------------------- props
def ell(c, x, y, rx, ry, fill, outline=True, n=24):
    pts = [(x + rx * math.cos(2 * math.pi * i / n), y + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
    c.poly(pts, fill, outline)


def cup(c, x, y, s=1.0, level=0.0, col=(255, 255, 255)):
    c.poly([(x - 32 * s, y - 56 * s), (x + 32 * s, y - 56 * s), (x + 23 * s, y), (x - 23 * s, y)], col, True)
    if level > 0:
        ly = y - 56 * s * level; wl = 32 - 9 * level
        c.poly([(x - (23 + 9 * level) * s * 0 - wl * s, ly), (x + wl * s, ly), (x + 23 * s, y), (x - 23 * s, y)], BLUE, False)
    c.line([(x + 32 * s, y - 42 * s), (x + 52 * s, y - 38 * s), (x + 52 * s, y - 16 * s), (x + 27 * s, y - 14 * s)], INK, .9)


def plate(c, x, y, s=1.0, col=CREAM): ell(c, x, y, 70 * s, 16 * s, col)


def stack(c, x, y, n, wob, t):
    for i in range(n):
        o = wob * math.sin(t * 5 + i * .7) * (i / max(1, n)) * 24
        plate(c, x + o, y - i * 20, 1.0, RAIN[i % 7] if i % 2 else CREAM)


def clock(c, x, y, r, a_min, a_hr):
    c.circ(x, y, r, fill=(255, 255, 255), w=1.4)
    for i in range(12): a = rad(i * 30); c.line([(x + r * .82 * math.sin(a), y - r * .82 * math.cos(a)), (x + r * .94 * math.sin(a), y - r * .94 * math.cos(a))], INK, .7)
    c.line([(x, y), (x + r * .78 * math.sin(rad(a_min)), y - r * .78 * math.cos(rad(a_min)))], INK, 1.1)
    c.line([(x, y), (x + r * .5 * math.sin(rad(a_hr)), y - r * .5 * math.cos(rad(a_hr)))], RED, 1.3)


def phone(c, x, y, s=1.0):
    c.poly([(x - 34 * s, y - 62 * s), (x + 34 * s, y - 62 * s), (x + 34 * s, y + 62 * s), (x - 34 * s, y + 62 * s)], (60, 64, 80))
    c.rect(x - 27 * s, y - 50 * s, x + 27 * s, y + 46 * s, fill=(150, 210, 255), outline=False)


def qmark(c, x, y, s=1.0, col=RED):
    pts = [(x + 24 * s * math.cos(rad(a)), y - 28 * s + 24 * s * math.sin(rad(a))) for a in range(200, 450, 18)] + [(x, y + 18 * s), (x, y + 30 * s)]
    c.line(pts, col, 1.6); c.circ(x, y + 56 * s, 6 * s, fill=col, outline=False)


def note(c, x, y, col, s=1.0):
    c.circ(x, y, 17 * s, fill=col); c.line([(x + 15 * s, y), (x + 15 * s, y - 70 * s), (x + 42 * s, y - 52 * s)], INK, 1.2)


def check(c, x, y, s=1.0, col=GRN):
    c.line([(x - 34 * s, y), (x - 8 * s, y + 28 * s), (x + 38 * s, y - 34 * s)], INK, 2.6 * s); c.line([(x - 34 * s, y), (x - 8 * s, y + 28 * s), (x + 38 * s, y - 34 * s)], col, 1.5 * s)


def cross(c, x, y, s=1.0, col=RED):
    for sg in (-1, 1): c.line([(x - 36 * s, y - 36 * s * sg), (x + 36 * s, y + 36 * s * sg)], col, 1.8 * s)


def bubble(c, x, y, s, tail_from=None, fill=(255, 255, 255)):
    if s <= 0.02: return
    for dx, dy, r in ((-70, 6, 78), (60, 8, 82), (0, -36, 84), (-30, 40, 66), (34, 42, 66)): c.circ(x + dx * s, y + dy * s, r * s, fill=fill, outline=False)
    for dx, dy, r in ((-70, 6, 78), (60, 8, 82), (0, -36, 84)): c.circ(x + dx * s, y + dy * s, r * s, fill=None, w=1.0)
    c.d  # keep canvas alive
    if tail_from:
        for i, r in ((1, 18), (2, 11)):
            u = i / 3.2; c.circ(x + (tail_from[0] - x) * u, y + 70 * s + (tail_from[1] - y - 70 * s) * u, r * s, fill=fill)


def spiral(c, x, y, r1, turns, rot, w=1.7, n=140):
    prev = None
    for i in range(n):
        u = i / (n - 1); a = rot + u * turns * 2 * math.pi; r = 8 + r1 * u
        q = (x + r * math.cos(a), y + r * math.sin(a))
        if prev: c.line([prev, q], RAIN[int(u * 14) % 7], w)
        prev = q


def hills(c, y0, cols, t=0.0):
    for j, col in enumerate(cols):
        pts = [(0, 1080)] + [(x, y0 + j * 90 + 60 * math.sin(x / 330 + j * 1.7) + 25 * math.sin(x / 120 + j)) for x in range(0, 1981, 60)] + [(1920, 1080)]
        c.poly(pts, col)


# ---------------------------------------------------------------- rooms
def living(c, bg=WALL):
    c.rect(0, 0, 1920, 1080, fill=bg, outline=False); c.rect(0, 820, 1920, 1080, fill=FLOOR, outline=False); c.line([(0, 820), (1920, 820)])
    c.rect(1380, 180, 1780, 560, fill=SKY); c.line([(1580, 180), (1580, 560)]); c.line([(1380, 370), (1780, 370)])


def couch(c):
    c.rect(220, 620, 820, 780, fill=PURP); c.rect(180, 700, 860, 880, fill=(130, 90, 215)); c.rect(180, 690, 260, 880, fill=(110, 76, 190)); c.rect(780, 690, 860, 880, fill=(110, 76, 190))
    c.rect(260, 760, 780, 790, fill=(180, 150, 245), outline=False)


def kitchen(c):
    c.rect(0, 0, 1920, 1080, fill=TEAL, outline=False); c.rect(0, 880, 1920, 1080, fill=(236, 214, 178), outline=False); c.line([(0, 880), (1920, 880)])
    c.rect(780, 740, 1920, 880, fill=(205, 160, 112)); c.rect(780, 724, 1920, 748, fill=(245, 238, 225))


# ---------------------------------------------------------------- scenes
def s_thirst(c, p, t, T):
    living(c); couch(c)
    keys = [(0, sit(ra1=75, ra2=160, la1=20, la2=40, mood="flat", look=0)), (.18, sit(ra1=80, ra2=165, mood="worry")),
            (.5, sit(lean=14, ra1=30, ra2=40, mood="open")), (.72, stand(560, lean=6, mood="open", ra1=10, ra2=20)),
            (.8, stand(600, mood="smile")), (1.0, stand(960, mood="smile"))]
    Z = pose_at(keys, p)
    if p > .78: Z = walk(Z, t, ease((p - .78) / .08))
    f = fig(c, Z)
    s = ease((p - .1) / .08) * (1 - ease((p - .52) / .05))
    bubble(c, Z["hx"] + 260, 300, s, tail_from=f["head"])
    if s > 0.05: cup(c, Z["hx"] + 260, 340 + 8 * math.sin(t * 3), 1.6 * s, level=.8)


def s_nocup(c, p, t, T):
    kitchen(c)
    c.rect(900, 150, 1700, 450, fill=(246, 244, 236))
    for i in range(3): c.line([(900 + i * 266.6, 150), (900 + i * 266.6, 450)])
    open_ = ease((p - .62) / .12)
    c.rect(1166, 150, 1433, 450, fill=(70, 62, 66), outline=True)
    c.line([(1166, 300), (1433, 300)], (110, 100, 104), 1.0)
    wd = 266 * (1 - open_ * .8); c.poly([(1166, 150), (1166 + wd, 160), (1166 + wd, 440), (1166, 450)], (255, 255, 250))
    keys = [(0, stand(240, mood="flat")), (.55, stand(1090, mood="flat", lean=3)), (.66, stand(1110, mood="worry", ra1=160, ra2=175)), (1, stand(1110, mood="worry", ra1=160, ra2=175, tilt=6))]
    Z = pose_at(keys, p)
    if p < .6: Z = walk(Z, t, 1.0)
    f = fig(c, Z)
    s = ease((p - .7) / .1)
    bubble(c, 800, 250, s, tail_from=f["head"])
    if s > .05: cup(c, 800, 285, 1.5 * s); cross(c, 800, 245, 1.5 * s)


def s_sink(c, p, t, T):
    kitchen(c)
    c.rect(1090, 660, 1500, 740, fill=(120, 170, 215)); c.line([(1560, 724), (1560, 560), (1480, 540)], INK, 1.6)
    stack(c, 1300, 650, 9, .5 + p * 1.6, t)
    keys = [(0, stand(640, mood="flat")), (.35, stand(640, mood="worry", ra1=150, ra2=210, la1=150, la2=210)), (1, stand(640, mood="tired", ra1=150, ra2=210, la1=150, la2=210, tilt=-6))]
    f = fig(c, pose_at(keys, p))
    s = ease((p - .4) / .12)
    bubble(c, 430, 230, s, tail_from=f["head"])
    if s > .05:
        c.rect(380 - 70 * s, 180 - 60 * s, 380 + 70 * s, 290, fill=(255, 255, 255)); c.rect(380 - 70 * s, 180 - 60 * s, 380 + 70 * s, 180 - 20 * s, fill=RED)
        cross(c, 380, 255, 1.3 * s)


def s_phone(c, p, t, T):
    kitchen(c)
    c.rect(1090, 660, 1500, 740, fill=(120, 170, 215)); stack(c, 1300, 650, 8, 0.4, t)
    scrub = p < .5
    Z = P(hx=960, mood="open" if not scrub else "flat", lean=8 if scrub else 0)
    if scrub: Z["ra1"] = 70 + 24 * math.sin(t * 13); Z["ra2"] = 100 + 24 * math.sin(t * 13)
    else: Z["look"] = math.sin(t * 5) * 1.2; Z["tilt"] = math.sin(t * 5) * 6; Z["ra1"] = 10; Z["ra2"] = 20
    f = fig(c, Z)
    if scrub: plate(c, f["rh"][0] + 40, f["rh"][1], .55, CREAM)
    else:
        s = ease((p - .52) / .1); bubble(c, 1000, 250, s, tail_from=f["head"])
        if s > .05: phone(c, 1000, 262 + 14 * math.sin(t * 7), 1.4 * s); qmark(c, 1090, 200, .9 * s)


def s_hour(c, p, t, T):  # abstract: the loop
    c.rect(0, 0, 1920, 1080, fill=(50, 34, 100), outline=False)
    for i in range(7): c.circ(960, 540, 130 + i * 62, fill=None, outline=False)
    spiral(c, 960, 540, 470, 4.2, t * 1.4, 2.0)
    clock(c, 960, 540, 190, t * 520, t * 43)
    for i, kind in enumerate(("phone", "plate", "cup", "x")):
        a = t * 1.1 + i * math.pi / 2; x, y = 960 + 600 * math.cos(a), 540 + 330 * math.sin(a)
        if kind == "phone": phone(c, x, y, .7)
        elif kind == "plate": plate(c, x, y, .8, CREAM)
        elif kind == "cup": cup(c, x, y + 28, .8)
        else: qmark(c, x, y - 10, .8, YEL)
    cup(c, 1650, 960, 1.0, 0.0)


def s_song(c, p, t, T):
    living(c, bg=(214, 190, 255)); c.rect(0, 820, 1920, 1080, fill=(150, 110, 200), outline=False); c.line([(0, 820), (1920, 820)])
    beat = abs(math.sin(t * math.pi * 2.2))
    Z = P(hx=960, hy=GROUND - 176 * K + 12 * beat, mood="smile", tilt=7 * math.sin(t * math.pi * 2.2), ra1=40 + 30 * math.sin(t * 9), ra2=70 + 30 * math.sin(t * 9),
          la1=-40 - 30 * math.sin(t * 9), la2=-20, rl1=6 * math.sin(t * 9), rl2=6 * math.sin(t * 9), ll1=-6 * math.sin(t * 9), ll2=-6 * math.sin(t * 9))
    f = fig(c, Z, headphones=True)
    for i in range(7):
        u = ((t * .32 + i / 7) % 1); x = 560 + i * 130 + 35 * math.sin(u * 8 + i); y = 760 - u * 640
        note(c, x, y, RAIN[(i + 2) % 7], .9 + .2 * math.sin(i))


def s_small(c, p, t, T):
    kitchen(c)
    c.rect(1090, 660, 1500, 740, fill=(120, 170, 215)); stack(c, 1300, 650, max(0, 8 - int(p * 8)), .2, t)
    scrub = p < .45
    Z = P(hx=900, mood="smile", lean=6 if scrub else 0)
    if scrub: Z["ra1"] = 70 + 20 * math.sin(t * 12); Z["ra2"] = 100 + 20 * math.sin(t * 12)
    f = fig(c, Z)
    if scrub: plate(c, f["rh"][0] + 40, f["rh"][1], .55, CREAM)
    cup(c, 1700, 724, 1.5, level=ease((p - .45) / .3))
    for i, th in enumerate((.12, .45, .78)):
        s = ease((p - th) / .08)
        if s > 0: check(c, 1470 + i * 130, 190, .9 * s)


def s_calm(c, p, t, T):
    living(c, bg=(255, 236, 190)); couch(c)
    Z = sit(lean=-5, mood="smile", ra1=20, ra2=30, la1=10, la2=20)
    f = fig(c, Z)
    u = ease(p * 1.1)
    x = 800 + 100 * u; y = 360 - 520 * u; s = max(.05, 1.0 - .8 * u)
    bubble(c, x, y, s, tail_from=f["head"] if p < .3 else None)
    spiral(c, x, y, 95 * s, 3.0, t * 1.6, 1.3)
    glow = ease(p)
    c.glow(1580, 370, 260 + 100 * glow, col=GOLD, strength=190)


def sunrise(c, q, t):
    for i in range(24):
        u = i / 23; col = (int(70 + 185 * u), int(60 + 120 * u), int(150 - 20 * u) if u < .5 else int(110 + 20 * u))
        c.rect(0, i * 46, 1920, i * 46 + 48, fill=col, outline=False)
    sy = 980 - 520 * ease(q); c.glow(960, sy, 480, col=GOLDL, strength=230)
    c.rays(960, sy, 150, 520, 28, 180 + 8 * math.sin(t), 360 - 8 * math.sin(t), YEL)
    c.circ(960, sy, 130, fill=YEL, w=1.2)
    for i in range(3):
        x = (300 + i * 650 + t * 20 * (i + 1)) % 2300 - 200; y = 250 + 90 * i
        for dx, dy, r in ((-50, 0, 46), (0, -18, 56), (56, 4, 44)): c.circ(x + dx, y + dy, r, fill=(255, 255, 255), outline=False)
    hills(c, 700, [(110, 170, 130), (80, 150, 120), (50, 120, 110)], t)
    for i in range(3):
        bx = (200 + t * 60 + i * 140) % 2100; by = 230 + 20 * math.sin(t * 3 + i) + i * 38
        c.line([(bx - 20, by - 8), (bx, by), (bx + 20, by - 8)], INK, .9)


def s_peace1(c, p, t, T): sunrise(c, .5 * p, t)
def s_peace2(c, p, t, T): sunrise(c, .5 + .5 * p, t)


RECIPES = {"thirsty": {"s001": s_thirst, "s002": s_nocup, "s003": s_sink, "s004": s_phone, "s005": s_hour,
                       "s006": s_song, "s007": s_small, "s008": s_calm, "s009": s_peace1, "s010": s_peace2}}


# ---------------------------------------------------------------- driver
def draw_frame(args):
    fn, p, t, T, seed, path = args
    c = Canvas(W, H, bg=(255, 255, 255), seed=seed); fn(c, p, t, T); c.save(path)


def wav_len(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return float(out.strip())


def cmd_voices(a):
    from kokoro_onnx import Kokoro
    import soundfile as sf
    d = os.environ.get("KOKORO_DIR", "."); K = Kokoro(os.path.join(d, "kokoro-v1.0.onnx"), os.path.join(d, "voices-v1.0.bin"))
    os.makedirs(os.path.join(a.assets, "vo"), exist_ok=True)
    for s in json.load(open(a.scenes))["scenes"]:
        au, sr = K.create(s["vo"], voice=a.voice, speed=a.speed, lang="en-us"); sf.write(os.path.join(a.assets, "vo", f"{s['id']}.wav"), au, sr)
        print(s["id"], f"{len(au) / sr:.1f}s")


def cmd_render(a):
    rec = RECIPES[a.recipes]; tmp = tempfile.mkdtemp(prefix="anim_")
    try:
        for s in json.load(open(a.scenes))["scenes"]:
            i = s["id"]; fn = rec[i]
            vo = os.path.join(a.assets, "vo", f"{i}.wav"); T = (wav_len(vo) if os.path.exists(vo) else s["est_sec"]) + HEAD + TAIL
            n = int(math.ceil(T * a.fps)); d = os.path.join(tmp, i); os.makedirs(d)
            jobs = [(fn, k / max(1, n - 1), k / a.fps, T, (k % 3) + 1, os.path.join(d, f"f{k:04d}.png")) for k in range(n)]
            with Pool() as pool: pool.map(draw_frame, jobs, chunksize=4)
            out = os.path.join(a.assets, f"{i}.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", os.path.join(d, "f%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
            shutil.rmtree(d); print(i, f"{n} frames, {T:.1f}s")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("voices"); v.add_argument("scenes"); v.add_argument("assets"); v.add_argument("--voice", default="am_michael"); v.add_argument("--speed", type=float, default=0.95)
    r = sub.add_parser("render"); r.add_argument("scenes"); r.add_argument("assets"); r.add_argument("--recipes", default="thirsty"); r.add_argument("--fps", type=int, default=12)
    a = ap.parse_args(); (cmd_voices if a.cmd == "voices" else cmd_render)(a)
