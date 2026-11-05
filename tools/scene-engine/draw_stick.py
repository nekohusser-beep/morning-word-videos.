#!/usr/bin/env python3
"""Free picture route: draws original stick-figure storybook scenes in code (no image tool, no credits).
  draw_stick.py SCENES.json OUT_DIR [--w 1920 --h 1080]
Each scene id needs a recipe in RECIPES (a list of drawing calls). Look: cream parchment, rough black ink,
gold accent, round-head stick figures. Use when no image tool is available or for fast tests."""
import argparse, json, math, os, random
from PIL import Image, ImageDraw, ImageFilter

INK = (36, 31, 28); PAPER = (244, 236, 216); GOLD = (200, 150, 62); GOLDL = (236, 205, 130)
ROBE = (150, 108, 74); GREY = (150, 148, 145); WATER = (150, 178, 196); GREEN = (178, 190, 140)
S = 2  # supersample


class Canvas:
    def __init__(s, w, h, bg=PAPER, seed=7):
        s.w, s.h = w * S, h * S; s.im = Image.new("RGB", (s.w, s.h), bg); s.d = ImageDraw.Draw(s.im, "RGBA")
        s.r = random.Random(seed); s.lw = max(6, h // 150) * S; s.u = h / 1080  # u = scale unit
        rnd = random.Random(3)
        for _ in range(900):  # paper grain
            x, y = rnd.randrange(s.w), rnd.randrange(s.h); c = rnd.randrange(-9, 4)
            s.d.point((x, y), fill=(bg[0] + c, bg[1] + c, bg[2] + c, 255))

    def P(s, x, y): return (x * s.u * S, y * s.u * S)  # design space 1920x1080 -> pixels

    def wob(s, pts, amt=2.2, step=26):
        out = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
            for k in range(n): t = k / n; out.append((x0 + (x1 - x0) * t + s.r.uniform(-amt, amt), y0 + (y1 - y0) * t + s.r.uniform(-amt, amt)))
        out.append(pts[-1]); return out

    def line(s, pts, col=INK, w=1.0):
        p = [s.P(*q) for q in s.wob(pts)]; s.d.line(p, fill=col, width=int(s.lw * w), joint="curve")
        for q in (p[0], p[-1]): r = s.lw * w / 2; s.d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)

    def poly(s, pts, fill, outline=True):
        s.d.polygon([s.P(*q) for q in pts], fill=fill)
        if outline: s.line(list(pts) + [pts[0]])

    def circ(s, x, y, r, fill=None, outline=True, w=1.0):
        a, b = s.P(x - r, y - r), s.P(x + r, y + r)
        if fill: s.d.ellipse([a, b], fill=fill)
        if outline:
            pts = [(x + r * math.cos(t / 20 * 2 * math.pi), y + r * math.sin(t / 20 * 2 * math.pi)) for t in range(21)]; s.line(pts, w=w)

    def rect(s, x0, y0, x1, y1, fill=None, outline=True):
        if fill: s.d.rectangle([s.P(x0, y0), s.P(x1, y1)], fill=fill)
        if outline: s.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])

    def glow(s, x, y, r, col=GOLD, strength=150):
        for k in range(12, 0, -1):
            rr = r * k / 12; a = int(strength * (1 - k / 12) ** 1.6 / 3 + 6)
            a0, b0 = s.P(x - rr, y - rr), s.P(x + rr, y + rr); s.d.ellipse([a0, b0], fill=col + (a,))

    def rays(s, x, y, r0, r1, n=14, a0=0, a1=360, col=GOLD):
        for k in range(n):
            t = math.radians(a0 + (a1 - a0) * k / max(n - 1, 1))
            s.line([(x + r0 * math.cos(t), y + r0 * math.sin(t)), (x + r1 * math.cos(t), y + r1 * math.sin(t))], col, 0.8)

    def save(s, path):
        im = s.im.filter(ImageFilter.GaussianBlur(0.4)).resize((s.w // S, s.h // S), Image.LANCZOS); im.save(path)


def figure(c, x, y, k=1.0, pose="stand", item=None, flip=1):
    """x,y = feet/base point in design space. pose: stand, bowed, sit, kneel."""
    H = 230 * k; hr = 34 * k
    if pose == "sit": H *= 0.72
    if pose == "kneel": H *= 0.68
    top = y - H; hx, hy = x + (22 * k * flip if pose in ("bowed", "kneel") else 0), top + hr + (14 * k if pose in ("bowed", "kneel") else 0)
    sh = (x, top + hr * 2 + 6 * k)
    # robe
    w0 = 44 * k; wb = (64 if pose != "sit" else 86) * k
    c.poly([(sh[0] - w0 * .5, sh[1]), (sh[0] + w0 * .5, sh[1]), (x + wb, y), (x - wb, y)], ROBE)
    c.line([(x - wb * .78, y - H * .34), (x + wb * .78, y - H * .34)], GOLD, 1.1)  # gold cord belt
    # arms
    hand_l = (x - 52 * k * flip, sh[1] + 78 * k); hand_r = (x + 52 * k * flip, sh[1] + 78 * k)
    if item == "phone": hand_l = (x + 26 * k * flip, sh[1] + 70 * k); hand_r = (x + 40 * k * flip, sh[1] + 78 * k)
    if pose == "kneel": hand_l = (x + 34 * k * flip, sh[1] + 54 * k); hand_r = (x + 48 * k * flip, sh[1] + 58 * k)
    c.line([(sh[0], sh[1] + 8 * k), hand_l]); c.line([(sh[0], sh[1] + 8 * k), hand_r])
    # head, eyes, beard
    c.circ(hx, hy, hr, fill=(252, 250, 244))
    for ex in (-11, 11): c.circ(hx + ex * k + (6 * k * flip if pose in ("bowed", "kneel") else 0), hy - 2 * k, 2.6 * k, fill=INK, outline=False)
    c.line([(hx - 18 * k, hy + 22 * k), (hx, hy + 40 * k), (hx + 18 * k, hy + 22 * k)], w=0.8)
    if item == "phone":
        px, py = hand_l; c.rect(px - 14 * k, py - 22 * k, px + 14 * k, py + 12 * k, fill=(250, 244, 220)); c.glow(px, py - 6 * k, 70 * k)
    return hand_l, hand_r, (hx, hy)


def sheep(c, x, y, k=1.0, flip=1):
    for dx, dy, r in ((-22, -34, 26), (4, -44, 30), (28, -32, 24), (4, -22, 28)): c.circ(x + dx * k, y + dy * k, r * k, fill=(252, 250, 244))
    c.circ(x + 46 * k * flip, y - 36 * k, 15 * k, fill=(90, 82, 76))
    for dx in (-14, 16): c.line([(x + dx * k, y - 6 * k), (x + dx * k, y + 14 * k)])


def bible(c, x, y, w=150, open_=True, k=1.0):
    w *= k
    if open_:
        c.poly([(x - w, y), (x, y - 12 * k), (x, y + 48 * k), (x - w, y + 60 * k)], (252, 250, 244))
        c.poly([(x + w, y), (x, y - 12 * k), (x, y + 48 * k), (x + w, y + 60 * k)], (252, 250, 244))
        for i in range(3):
            for sgn in (-1, 1): c.line([(x + sgn * w * .18, y + 8 * k + i * 12 * k), (x + sgn * w * .8, y + 6 * k + i * 12 * k + sgn * -3 * k)], GREY, .5)
    else:
        c.poly([(x - w * .5, y), (x + w * .5, y), (x + w * .5, y + 40 * k), (x - w * .5, y + 40 * k)], (96, 66, 48))
        c.line([(x, y + 6 * k), (x, y + 34 * k)], GOLD); c.line([(x - 10 * k, y + 18 * k), (x + 10 * k, y + 18 * k)], GOLD)


def hills(c, base=700, col=GREEN, n=3, seed=2):
    r = random.Random(seed)
    for i in range(n):
        y0 = base + i * 70; pts = [(0, 1080)]
        for xx in range(0, 1981, 60): pts.append((xx, y0 - 70 * math.sin(xx / 330 + i * 1.7) - 40 * i * 0 + r.uniform(-4, 4)))
        pts.append((1920, 1080)); c.poly(pts, tuple(int(col[j] * (1 - 0.08 * i)) for j in range(3)))


def sun(c, x, y, r=70):
    c.glow(x, y, r * 3.4); c.circ(x, y, r, fill=GOLDL); c.rays(x, y, r * 1.3, r * 1.9, 16)


def scribbles(c, x, y, k=1.0, n=7):
    r = random.Random(11)
    for i in range(n):
        ox, oy = x + r.uniform(-260, 260) * k, y + r.uniform(-60, 60) * k
        c.circ(ox, oy, r.uniform(40, 70) * k, fill=(210, 208, 204, 160))
        a = r.uniform(-.4, .4); c.poly([(ox - 24, oy - 16), (ox + 24, oy - 16), (ox + 24, oy + 16), (ox - 24, oy + 16)], (255, 255, 250))
        c.line([(ox - 24, oy - 16), (ox, oy + 2), (ox + 24, oy - 16)], GREY, .6)


def stars(c, n=60, seed=5, ymax=520):
    r = random.Random(seed)
    for _ in range(n): c.circ(r.uniform(20, 1900), r.uniform(20, ymax), r.uniform(2, 5), fill=GOLDL, outline=False)


def sky_gradient(c, top, bottom, h=1080):
    for yy in range(0, h, 4):
        t = yy / h; col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        c.d.rectangle([c.P(0, yy), c.P(1920, yy + 4)], fill=col + (255,))


def tent(c, x, y, k=1.0):
    c.poly([(x - 70 * k, y), (x, y - 80 * k), (x + 70 * k, y)], (200, 180, 140)); c.line([(x, y - 80 * k), (x, y)], w=.7)


# ---------- recipes for the Psalm 23 sample ----------
def s001(c):
    c.rect(0, 0, 1920, 1080, fill=(222, 210, 188), outline=False)
    for yy in range(80, 1080, 110):
        for xx in range(-60 + (yy // 110 % 2) * 90, 1980, 180): c.line([(xx, yy), (xx + 150, yy)], (200, 188, 164), .5)
    c.poly([(380, 760), (1180, 760), (1180, 1000), (380, 1000)], (176, 140, 104))
    c.poly([(380, 740), (1180, 740), (1180, 770), (380, 770)], (232, 224, 204))
    figure(c, 760, 760, 1.2, "sit", item="phone"); bible(c, 1500, 800, 90, open_=False)
    c.line([(1440, 842), (1440, 1000)]); c.line([(1560, 842), (1560, 1000)])


def s002(c):
    hills(c, 800, (200, 196, 176), 2); figure(c, 960, 960, 1.5, "bowed"); scribbles(c, 960, 270, 1.4)


def s003(c):
    c.poly([(420, 800), (1500, 800), (1500, 840), (420, 840)], (176, 140, 104)); c.line([(520, 840), (520, 1040)]); c.line([(1400, 840), (1400, 1040)])
    c.glow(1100, 740, 360); bible(c, 1100, 770, 170); c.rays(1100, 740, 120, 380, 11, 215, 325)
    figure(c, 640, 840, 1.25, "sit")


def s004(c):
    c.glow(960, 560, 700); c.rays(960, 560, 260, 700, 22); bible(c, 960, 600, 330)


def s005(c):
    sun(c, 1500, 360, 70); hills(c, 640, GREEN, 3)
    c.poly([(0, 900), (1920, 900), (1920, 960), (0, 960)], WATER, outline=False)
    for i in range(7): c.line([(120 + i * 270, 930), (230 + i * 270, 922), (300 + i * 270, 934)], (110, 140, 160), .6)
    c.line([(620, 880), (620, 520)], (110, 80, 56), 1.5); c.line([(620, 520), (640, 470), (590, 440)], (110, 80, 56), 1.5)


def s006(c):
    hills(c, 740, GREEN, 2); figure(c, 960, 930, 1.35)
    for x, y, f in ((620, 960, 1), (780, 1010, 1), (1190, 1005, -1), (1330, 950, -1), (480, 900, 1), (1470, 910, -1)): sheep(c, x, y, 1.15, f)


def s007(c):
    hills(c, 760, GREEN, 2); h = figure(c, 780, 930, 1.45, "stand")
    c.line([(h[0][0] - 30, h[0][1] + 150), (h[0][0] + 30, h[0][1] - 140)], (110, 80, 56), 1.6)
    c.line([(h[0][0] + 30, h[0][1] - 140), (h[0][0] + 70, h[0][1] - 175), (h[0][0] + 10, h[0][1] - 190)], (110, 80, 56), 1.6)
    for x, y, f in ((1250, 880, 1), (1500, 960, 1), (1700, 880, 1), (1400, 790, 1)): sheep(c, x, y, 1.0, f)


def s008(c):
    hills(c, 800, (205, 200, 178), 2); pts = [(300, 960)]
    r = random.Random(4)
    for i in range(8):
        cx, cy = 420 + i * 150, 900 - i * 40
        for t in range(0, 360, 30): pts.append((cx + 70 * math.cos(math.radians(t * (1 if i % 2 else -1))), cy + 40 * math.sin(math.radians(t * (1 if i % 2 else -1)))))
    pts.append((1620, 640)); c.line(pts, GREY, .9); tent(c, 1700, 640, 1.2); figure(c, 270, 990, 1.15, "stand")


def s009(c):
    c.rect(0, 0, 1920, 1080, fill=(228, 218, 196), outline=False)
    c.poly([(0, 860), (1920, 860), (1920, 1080), (0, 1080)], (196, 176, 146))
    c.poly([(1060, 800), (1500, 800), (1500, 880), (1060, 880)], (170, 160, 146))
    c.glow(1280, 700, 420, strength=200); c.line([(1280, 790), (1268, 740), (1292, 700), (1280, 660)], GOLD, 1.6); c.circ(1280, 740, 16, fill=GOLDL, outline=False)
    bible(c, 1700, 930, 90, k=.9); figure(c, 760, 900, 1.35, "kneel")


def s010(c):
    sky_gradient(c, (28, 36, 70), (236, 190, 120)); stars(c, 55, ymax=460); sun(c, 960, 640, 60)
    for i, col in enumerate(((46, 50, 70), (64, 62, 72))): 
        pts = [(0, 1080)] + [(xx, 700 + i * 90 - 60 * math.sin(xx / 300 + i * 2)) for xx in range(0, 1981, 60)] + [(1920, 1080)]
        c.poly(pts, col, outline=False)
    c.poly([(930, 700), (990, 700), (1500, 1080), (420, 1080)], GOLD + (150,), outline=False); c.glow(960, 700, 300)


def s_tired(c):
    hills(c, 820, (200, 196, 176), 2); figure(c, 960, 960, 1.55, "standbowed" if False else "bowed")


def s_read(c):
    hills(c, 760, GREEN, 2); sun(c, 1560, 330, 60); c.glow(1250, 930, 300, strength=200); bible(c, 1250, 950, 140, k=.9)
    figure(c, 700, 960, 1.4, "kneel")


def s_flame(c):
    c.rect(0, 0, 1920, 1080, fill=(228, 218, 196), outline=False)
    c.poly([(0, 860), (1920, 860), (1920, 1080), (0, 1080)], (196, 176, 146))
    c.poly([(760, 800), (1160, 800), (1160, 880), (760, 880)], (170, 160, 146))
    c.glow(960, 700, 460, strength=210); c.line([(960, 790), (948, 740), (972, 700), (960, 660)], GOLD, 1.8); c.circ(960, 740, 18, fill=GOLDL, outline=False)
    bible(c, 1400, 930, 100, k=.9)


# new scene ids -> recipe (Psalm 23 sample, 12 scenes)
RECIPES = {"s001": s001, "s002": s002, "s003": s_tired, "s004": s003, "s005": s004, "s006": s005, "s007": s006, "s008": s007,
           "s009": s008, "s010": s_flame, "s011": s_read, "s012": s010}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("scenes"); ap.add_argument("out")
    ap.add_argument("--w", type=int, default=1920); ap.add_argument("--h", type=int, default=1080); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for s in json.load(open(a.scenes))["scenes"]:
        f = RECIPES.get(s["id"])
        if not f: print("no recipe for", s["id"]); continue
        c = Canvas(a.w, a.h); f(c); c.save(os.path.join(a.out, s["id"] + ".png")); print("drew", s["id"])
