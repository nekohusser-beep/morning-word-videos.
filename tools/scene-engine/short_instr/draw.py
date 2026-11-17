#!/usr/bin/env python3
"""Short 3: The Instructions (vertical 9:16). Instruction-gag format: an off-screen instructor gives a two-part
instruction, the stick figure acts on half one, half two lands, he freezes. Reuses the vertical rig from short_thirsty.
  draw.py voices SCENES ASSETS      Kokoro voice per scene (scene's own voice/speed) -> ASSETS/vo/sNNN.wav
  draw.py render SCENES ASSETS [--fps 12] [--only s001 ...]
Clip length = HEAD + voice + hold (silent action after the voice) + TAIL. Recipes read INFO (voice start/end) so
the figure moves on the instructor's words, not on a fixed clock."""
import argparse, json, math, os, sys, subprocess, tempfile, shutil
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "short_thirsty")); sys.path = [p for p in sys.path if not p.endswith("short_instr")]
import draw as V
from draw import (W, H, G, K, HIP, SEAT, stand, sit, F, room, title, ease, pose_at, P, qmark, check, cross,
                  INK, GOLD, GOLDL, SKY, WALL, FLOOR, TEAL, PINK, PURP, YEL, GRN, BLUE, RED, ORANGE, CREAM, RAIN)
from anim_stick import ell, rad, clock
from PIL import ImageFont, ImageDraw

HEAD, TAIL = 0.15, 0.35
HX = 600                      # figure hip x (seated, facing right)
TOP = 1235                    # table top
COFFEE = (96, 58, 36); MUGC = (235, 110, 80); SALTC = (250, 250, 255); CAP = (110, 150, 220); SUGC = (255, 170, 200)
INFO = {"sp0": HEAD, "sp1": HEAD + 3.0, "T": 6.0, "hold": 2.0}   # filled per scene at render time
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"


# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def seg(t, a, b): return ease((t - a) / max(1e-6, b - a))


def arm_to(Z, target, face=1, k=K):
    """Two-link IK for the front arm: sets ra1/ra2 so the hand lands on target."""
    TL, L1, L2 = 130 * k, 68 * k, 60 * k
    sx = Z["hx"] + face * math.sin(rad(Z["lean"])) * TL; sy = Z["hy"] - math.cos(rad(Z["lean"])) * TL
    vx, vy = (target[0] - sx) * face, target[1] - sy
    d = min(math.hypot(vx, vy), L1 + L2 - 1e-3); phi = math.atan2(vx, vy)
    beta = math.acos(max(-1, min(1, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
    a1 = phi - beta
    ex, ey = L1 * math.sin(a1), L1 * math.cos(a1)
    a2 = math.atan2(vx - ex, vy - ey)
    Z["ra1"], Z["ra2"] = math.degrees(a1), math.degrees(a2)
    return Z


def label(c, text, x, y, size=34, col=INK):
    f = ImageFont.truetype(FONT, int(size * 2)); d = ImageDraw.Draw(c.im, "RGBA"); tw = d.textlength(text, font=f) / 2
    d.text(((x - tw / 2) * 2, (y - size * .62) * 2), text, font=f, fill=col + (255,))


# ---------------------------------------------------------------- props
def backdrop(c):
    room(c, wall=(255, 232, 186), floor=(222, 170, 120), window=False)
    c.rect(60, 620, 320, 940, fill=SKY); c.line([(190, 620), (190, 940)]); c.line([(60, 780), (320, 780)])
    clock(c, 560, 740, 100, 40, 300)   # wall clock, quiet decor   # window left


def table(c):
    c.rect(640, TOP, W + 40, TOP + 34, fill=(176, 120, 78)); c.line([(700, TOP + 34), (700, G)], INK, 1.5); c.line([(1030, TOP + 34), (1030, G)], INK, 1.5)
    c.rect(690, TOP + 34, 1040, TOP + 60, fill=(150, 100, 64), outline=False)


def chair(c):
    c.rect(HX - 190, 900, HX - 150, G, fill=(130, 90, 60)); c.rect(HX - 190, 900, HX - 90, 960, fill=(150, 104, 70))
    c.rect(HX - 190, 1340, HX - 20, 1368, fill=(150, 104, 70)); c.line([(HX - 40, 1368), (HX - 40, G)], INK, 1.5)


def mug(c, x, y, salt=0, level=0.78, stir=0.0, spill=0.0, fresh=False, steam_t=0.0):
    """Coffee mug resting at (x, y=bottom). salt = number of white specks floating."""
    c.rect(x - 52, y - 104, x + 52, y, fill=MUGC)
    c.line([(x + 52, y - 84), (x + 92, y - 78), (x + 94, y - 36), (x + 52, y - 28)], INK, 1.6)
    ell(c, x, y - 104, 52, 14, COFFEE)
    if fresh: ell(c, x - 10, y - 108, 18, 4, (190, 140, 100), outline=False)
    for i in range(int(salt)):
        a = i * 2.4 + stir * 3.0 * (0.5 + 0.5 * (i % 3) / 2); r = (14 + (i * 7) % 30) * (1 if stir else 1)
        px, py = x + math.cos(a) * min(r, 42) , y - 104 + math.sin(a) * min(r, 42) * 0.26
        c.circ(px, py, 4.2, fill=(250, 250, 255), outline=False)
    if stir > 0:
        for j in range(2): c.line([(x + 40 * math.cos(stir * 9 + j * 3.1), y - 104 + 11 * math.sin(stir * 9 + j * 3.1)), (x + 8 * math.cos(stir * 9 + j * 3.1 + 1.4), y - 104 + 2 * math.sin(stir * 9 + j * 3.1 + 1.4))], (170, 120, 90), .8)
    if spill > 0:
        for i, dx in enumerate((-46, 52, 58)):
            u = clamp(spill * 1.4 - i * 0.25)
            if u > 0: c.circ(x + dx + (8 if dx > 0 else -8) * u, y - 100 + 70 * u * u, 7 - 2 * u, fill=COFFEE, outline=False)
    if fresh or level == 0:
        for j in range(3): c.line([(x - 16 + j * 16 + 5 * math.sin(steam_t * 3 + j), y - 130 - k) for k in (0, 18, 36)], (200, 200, 205), .9)


def shaker(c, x, y, tilt=0.0, inverted=False, z=1.35):
    """Salt shaker whose BASE center is at (x, y) when upright; inverted draws it cap-down with the cap at (x, y)."""
    s = -1 if inverted else 1
    c.poly([(x - 24 * z, y), (x + 24 * z, y), (x + 20 * z, y - s * 74 * z), (x - 20 * z, y - s * 74 * z)], SALTC)
    c.poly([(x - 21 * z, y - s * 74 * z), (x + 21 * z, y - s * 74 * z), (x + 17 * z, y - s * 98 * z), (x - 17 * z, y - s * 98 * z)], CAP)
    for dx in (-8, 0, 8): c.circ(x + dx * z, y - s * 90 * z, 2.2, fill=INK, outline=False)
    label(c, "SALT", x, y - s * 36 * z, 20, (70, 80, 120))


def sugar(c, x, y):
    ell(c, x, y - 70, 54, 40, SUGC); c.rect(x - 56, y - 76, x + 56, y, fill=SUGC)
    c.poly([(x - 56, y - 76), (x + 56, y - 76), (x + 36, y - 114), (x - 36, y - 114)], (255, 215, 130)); c.circ(x, y - 124, 9, fill=INK)
    label(c, "SUGAR", x, y - 38, 19, (150, 60, 100))


def spoon(c, x, y, ang=8):
    """Spoon lying on the table with its bowl at left; x,y = center."""
    c.line([(x - 40, y), (x + 70, y - 6)], (190, 190, 200), 1.3); c.circ(x - 54, y, 15, fill=(215, 215, 225))


def napkin(c, x, y): c.poly([(x - 70, y), (x + 70, y), (x + 62, y - 14), (x - 62, y - 14)], (255, 255, 255))


def speaker(c, t, speaking, y0=640):
    """Off-screen instructor marker: speaker icon top right, rings pulse while the voice runs."""
    x, y = 900, y0
    c.rect(x - 80, y - 54, x + 80, y + 78, fill=(255, 255, 255)); label(c, "INSTRUCTOR", x, y + 56, 20, (70, 70, 80))
    c.poly([(x - 40, y - 10), (x - 20, y - 10), (x + 4, y - 30), (x + 4, y + 20), (x - 20, y), (x - 40, y)], (70, 70, 80))
    n = 3 if speaking else 0
    for i in range(n):
        u = ((t * 1.8 + i / 3.0) % 1.0); r = 16 + 26 * u
        pts = [(x + 6 + r * math.cos(math.radians(a)), y - 5 + r * math.sin(math.radians(a))) for a in range(-50, 51, 10)]
        c.line(pts, (70, 70, 80) if u < .6 else (170, 170, 180), 1.0)


def dots(c, x, y, s=1.0):   # the frozen "..." note
    for i in range(3): c.circ(x + (i - 1) * 54 * s, y, 13 * s, fill=INK, outline=False)


def sweat(c, x, y, u):
    y2 = y + 90 * u
    c.poly([(x, y2 - 26), (x + 14, y2 + 4), (x, y2 + 16), (x - 14, y2 + 4)], (150, 205, 255))


# ---------------------------------------------------------------- scene logic
def seated(arm_target=None, **kw):
    Z = sit(hx=HX, lean=kw.pop("lean", 14), **kw)
    Z.update(la1=14, la2=30)    # back arm resting
    if arm_target: arm_to(Z, arm_target)
    return Z


def idle_pose(t, mood="flat"): return seated(None, mood=mood, ra1=22, ra2=52)


def salting(c, t, t_start, shake_until, grains, mood="smile"):
    """Figure reaches for the shaker (starts at t_start), lifts over the mug and shakes. Returns (Z, shaker_pos|None, shaking, done_flag)."""
    SX, SY = 860, TOP - 52           # shaker on table
    MX = 930                         # mug x
    HOLD = (MX - 8, 1005)            # hand position above mug
    a = seg(t, t_start, t_start + 0.55); b = seg(t, t_start + 0.55, t_start + 1.0)
    rest = (HX + 150, 1215)
    if t < t_start: tgt = rest
    elif b <= 0: tgt = (rest[0] + (SX - rest[0]) * a, rest[1] + (SY - rest[1]) * a - 40 * math.sin(a * math.pi))
    else: tgt = (SX + (HOLD[0] - SX) * b, SY + (HOLD[1] - SY) * b - 70 * math.sin(b * math.pi))
    shaking = (b >= 1) and (t < shake_until)
    if shaking: tgt = (tgt[0] + 14 * math.sin(t * 34), tgt[1] + 22 * abs(math.sin(t * 34)))
    return tgt, b, shaking


def s01(c, p, t, T):
    backdrop(c); chair(c); table(c); sugar(c, 740, TOP); mug(c, 930, TOP, salt=0, steam_t=t)
    sp0, sp1 = INFO["sp0"], INFO["sp1"]; ts = sp1 - 0.35          # reaches as the words "salt shaker" land
    tgt, b, shaking = salting(c, t, ts, 1e9, 0)
    held = t >= ts + 0.5
    if not held: shaker(c, 860, TOP)
    Z = seated(tgt, mood="smile" if t > ts + 0.2 else "flat")
    f = F(c, Z)
    if held:
        hx_, hy_ = f["rh"]; shaker(c, hx_ + 12, hy_ + 70, inverted=True)
        if b >= 1:
            n = int((t - ts - 1.0) * 14)
            for i in range(max(0, min(n, 30))):
                u = ((t * 3.0 + i * .37) % 1.0); c.circ(hx_ + 10 + 6 * math.sin(i * 2.1), hy_ + 70 + 90 + u * (TOP - 104 - hy_ - 160), 3.6, fill=(250, 250, 255), outline=False)
    speaker(c, t, sp0 <= t < sp1)
    title(c, "POV: instructions", 540, 250, 84); title(c, "with an ADHD brain", 540, 390, 62, bg=(255, 255, 255), rot=2)


def s02(c, p, t, T):
    backdrop(c); chair(c); table(c); sugar(c, 740, TOP)
    sp0, sp1 = INFO["sp0"], INFO["sp1"]; frz = sp0 + 0.55 * (sp1 - sp0)
    MX = 930; HOLD = (MX - 8, 1005)
    shaking = t < frz
    tgt = (HOLD[0] + (14 * math.sin(t * 34) if shaking else 0), HOLD[1] + (22 * abs(math.sin(t * 34)) if shaking else 0))
    mood = "smile" if shaking else "worry"
    Z = seated(tgt, mood=mood, look=0 if shaking else min(1.5, (t - frz) * 3), tilt=0 if shaking else -4 * seg(t, frz, frz + .4))
    mug(c, MX, TOP, salt=int(8 + 20 * seg(t, 0, frz)), steam_t=t)
    f = F(c, Z); hx_, hy_ = f["rh"]; shaker(c, hx_ + 12, hy_ + 70, inverted=True)
    if shaking:
        for i in range(20):
            u = ((t * 3.0 + i * .37) % 1.0); c.circ(hx_ + 10 + 6 * math.sin(i * 2.1), hy_ + 70 + 90 + u * (TOP - 104 - hy_ - 160), 3.6, fill=(250, 250, 255), outline=False)
    s = seg(t, frz + .35, frz + .65)
    if s > .02: dots(c, f["head"][0] + 130, f["head"][1] - 150, s)
    speaker(c, t, sp0 <= t < sp1)


def bar(c, y, split=540, lit=1.0, reach=None, label_on=True, ok2=False):
    """The instruction as a bar: PART 1 (left) and PART 2 (right)."""
    x0, x1, h = 90, 990, 150
    c.rect(x0, y, split, y + h, fill=(120, 205, 140) if lit > 0 else (220, 220, 225)); c.rect(split, y, x1, y + h, fill=(225, 225, 232) if not ok2 else (120, 205, 140))
    label(c, "PART 1", (x0 + split) / 2, y + 76, 54, INK); label(c, "PART 2", (split + x1) / 2, y + 76, 54, INK if ok2 else (120, 120, 130))


def s03(c, p, t, T):   # abstract: he did one
    sp0, sp1 = INFO["sp0"], INFO["sp1"]
    c.rect(0, 0, W, H, fill=(255, 244, 214), outline=False)
    c.glow(540, 960, 520, col=GOLDL, strength=140)
    y = 900; bar(c, y)
    label(c, "one sentence, two parts", 540, 700, 58, INK)
    # ball runs part 1, then leaves the bar
    run = seg(t, sp0 + 0.2, sp0 + 0.9 * (sp1 - sp0) * 0.55); hop = seg(t, sp0 + 0.55 * (sp1 - sp0) + 0.1, sp1 + 0.9)
    bx = 120 + (540 - 120) * run if hop <= 0 else 540 + 260 * hop
    by = y - 36 - 6 * abs(math.sin(t * 16)) * (1 if hop <= 0 and run > 0 else 0)
    if hop > 0: by = y - 36 - 330 * math.sin(min(1, hop * 1.0) * math.pi) + 900 * max(0, hop - .55) ** 2
    c.circ(bx, by, 36, fill=YEL, w=1.2)
    if run >= 1: check(c, 315, y - 80, 1.6)
    if hop > .15: qmark(c, 765, y - 86, 1.4, RED)
    speaker(c, t, sp0 <= t < sp1, 470)
    title(c, "the instruction", 540, 250, 76, bg=(255, 255, 255))


def s04(c, p, t, T):
    backdrop(c); chair(c); table(c)
    sp0, sp1 = INFO["sp0"], INFO["sp1"]; ts = sp1 - 0.4          # grabs spoon as the word "spoon" lands
    SPX, SPY = 760, TOP - 14
    sugar(c, 1000, TOP) if False else None
    shaker(c, 1030, TOP)                                          # shaker now at the far end (beat 1 done)
    napkin(c, 760, TOP)
    MX = 930
    a = seg(t, ts, ts + .5); b = seg(t, ts + .5, ts + .9)
    rest = (HX + 150, 1215); swirl = max(0.0, t - (ts + .9))
    if b <= 0: tgt = (rest[0] + (SPX - 54 - rest[0]) * a, rest[1] + (SPY - 20 - rest[1]) * a)
    else: tgt = ((SPX - 54) + (MX - SPX + 54) * b + (22 * math.cos(swirl * 20) if b >= 1 else 0), (SPY - 20) + (1060 - SPY + 20) * b + (8 * math.sin(swirl * 20) if b >= 1 else 0) - 60 * math.sin(b * math.pi))
    Z = seated(tgt, mood="open" if t > ts else "flat")
    mug(c, MX, TOP, salt=22, stir=swirl, spill=clamp((swirl - .4) * 0.7), steam_t=t)
    held = t >= ts + .45
    if not held: spoon(c, SPX, SPY)
    f = F(c, Z)
    if held:
        hx_, hy_ = f["rh"]; c.line([(hx_ - 4, hy_ - 10), (hx_ + 10, hy_ + 100)], (190, 190, 200), 1.3); c.circ(hx_ + 12, hy_ + 112, 15, fill=(215, 215, 225))
    speaker(c, t, sp0 <= t < sp1)


def s05(c, p, t, T):
    backdrop(c); chair(c); table(c); shaker(c, 1030, TOP); napkin(c, 760, TOP)
    sp0, sp1 = INFO["sp0"], INFO["sp1"]; frz = sp0 + 0.35 * (sp1 - sp0)
    MX = 930; swirl = max(0.0, t - sp0) if t < frz else max(0.0, frz - sp0)
    tgt = (MX - 8 + (22 * math.cos(swirl * 20)), 1060 + 8 * math.sin(swirl * 20))
    Z = seated(tgt, mood="open" if t < frz else "worry", look=0 if t < frz else min(1.5, (t - frz) * 3))
    mug(c, MX, TOP, salt=22, stir=1.0 + swirl, spill=clamp(.5 + (swirl) * .3), steam_t=t if t < frz else frz)
    f = F(c, Z); hx_, hy_ = f["rh"]; c.line([(hx_ - 4, hy_ - 10), (hx_ + 10, hy_ + 100)], (190, 190, 200), 1.3); c.circ(hx_ + 12, hy_ + 112, 15, fill=(215, 215, 225))
    s = seg(t, frz + .4, frz + .7)
    if s > .02: dots(c, f["head"][0] + 130, f["head"][1] - 150, s)
    speaker(c, t, sp0 <= t < sp1)


def eyes_wide(c, head, k, lookx=0.0, blink=0.0):
    hx_, hy_ = head; ey = hy_ - 6 * k
    for sx in (-1, 1):
        ex = hx_ + sx * 14 * k
        c.circ(ex, ey, 15 * k * .8, fill=(255, 255, 255), w=.8)
        if blink > .5: c.rect(ex - 16, ey - 3, ex + 16, ey + 3, fill=(255, 248, 236), outline=False); c.line([(ex - 14, ey), (ex + 14, ey)], INK, .8)
        else: c.circ(ex + lookx, ey, 5.5 * k * .8, fill=INK, outline=False)


def s06(c, p, t, T):   # stares at camera
    backdrop(c); chair(c); table(c); shaker(c, 1030, TOP); napkin(c, 760, TOP)
    sp0, sp1 = INFO["sp0"], INFO["sp1"]
    MX = 930
    Z = seated(None, mood="flat", ra1=60, ra2=96, tilt=-2)
    Z["ra1"], Z["ra2"] = 54, 98
    mug(c, MX, TOP, salt=22, stir=0, steam_t=0)
    f = F(c, Z)
    hx_, hy_ = f["rh"]; c.line([(hx_ - 4, hy_ - 10), (hx_ + 6, hy_ + 60)], (190, 190, 200), 1.3)
    # spoon stays in the mug: draw handle sticking up from mug
    c.line([(MX + 14, TOP - 104), (MX + 44, TOP - 196)], (190, 190, 200), 1.3); c.circ(MX + 48, TOP - 206, 12, fill=(215, 215, 225))
    wide = seg(t, sp0 + .2, sp0 + .6); bl = 1.0 if (int(t * 1.7) % 4 == 3 and (t * 1.7) % 1 < .16) else 0.0
    eyes_wide(c, f["head"], K * (1 + .15 * wide), 0.0, bl)
    u = seg(t, sp1 + .2, sp1 + 1.6)
    if u > .02: sweat(c, f["head"][0] + 95, f["head"][1] - 40, u)
    speaker(c, t, sp0 <= t < sp1)


def s07(c, p, t, T):   # abstract: wait for the whole sentence
    sp0, sp1 = INFO["sp0"], INFO["sp1"]
    c.rect(0, 0, W, H, fill=(224, 244, 232), outline=False)
    c.glow(540, 960, 520, col=(180, 230, 190), strength=150)
    y = 900; run = seg(t, sp1 - .6, sp1 + .9)
    fill1 = 1.0
    bar(c, y, ok2=run >= 1)
    label(c, "let it finish", 540, 700, 62, INK)
    bx = 120 + 780 * run if run > 0 else 120
    by = y - 36 - 6 * abs(math.sin(t * 16)) * (1 if 0 < run < 1 else 0)
    c.circ(bx, by, 36, fill=YEL, w=1.2)
    if run >= 1: check(c, 315, y - 80, 1.6); check(c, 765, y - 80, 1.6)
    title(c, "same sentence", 540, 250, 76, bg=(255, 255, 255))


def s08(c, p, t, T):   # calm: waits, then picks up the spoon
    backdrop(c); chair(c); table(c); napkin(c, 760, TOP)
    sp0, sp1 = INFO["sp0"], INFO["sp1"]; ts = sp1 - .3
    MX = 930; SPX, SPY = 760, TOP - 14
    a = seg(t, ts, ts + .5); b = seg(t, ts + .5, ts + 1.0)
    rest = (HX + 150, 1215)
    tgt = rest if a <= 0 else ((rest[0] + (SPX - 54 - rest[0]) * a, rest[1] + (SPY - 20 - rest[1]) * a) if b <= 0 else ((SPX - 54) + (MX - SPX + 54) * b, SPY - 20 + (1060 - SPY + 20) * b - 60 * math.sin(b * math.pi)))
    Z = seated(tgt, mood="smile")
    mug(c, MX, TOP, salt=0, fresh=True, steam_t=t)
    held = a >= .6
    if not held: spoon(c, SPX, SPY)
    f = F(c, Z)
    if held:
        hx_, hy_ = f["rh"]; c.line([(hx_ - 4, hy_ - 10), (hx_ + 10, hy_ + 100)], (190, 190, 200), 1.3); c.circ(hx_ + 12, hy_ + 112, 15, fill=(215, 215, 225))
    s = seg(t, sp0 + .3, sp0 + .6)
    if s > .02: title(c, "Let them finish.", 540, 270, int(80 * s), bg=(255, 255, 255)); title(c, "Then the spoon.", 540, 410, int(80 * s), bg=YEL)
    if b >= 1: check(c, 560, 1000, 1.5)


RECIPES = {f"s{i:03d}": fn for i, fn in enumerate((s01, s02, s03, s04, s05, s06, s07, s08), 1)}


# ---------------------------------------------------------------- render
def draw_frame(args):
    fn, p, t, T, seed, path, info = args
    INFO.update(info)
    c = V.VCanvas(W, H, bg=(255, 255, 255), seed=seed); fn(c, p, t, T); c.save(path)


def wav_len(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip())


def cmd_voices(a):
    from kokoro_onnx import Kokoro
    import soundfile as sf
    d = os.environ.get("KOKORO_DIR", "."); Kk = Kokoro(os.path.join(d, "kokoro-v1.0.onnx"), os.path.join(d, "voices-v1.0.bin"))
    os.makedirs(os.path.join(a.assets, "vo"), exist_ok=True)
    for s in json.load(open(a.scenes))["scenes"]:
        au, sr = Kk.create(s["vo"], voice=s["voice"], speed=s["speed"], lang="en-us"); sf.write(os.path.join(a.assets, "vo", f"{s['id']}.wav"), au, sr); print(s["id"], s["voice"], f"{len(au) / sr:.2f}s", len(s["vo"].split()), "words")


def cmd_render(a):
    tmp = tempfile.mkdtemp(prefix="short_")
    try:
        for s in json.load(open(a.scenes))["scenes"]:
            if a.only and s["id"] not in a.only: continue
            i = s["id"]; fn = RECIPES[i]; vo = os.path.join(a.assets, "vo", f"{i}.wav")
            vd = wav_len(vo) if os.path.exists(vo) else s["est_sec"]; hold = s.get("hold", 0.0)
            T = vd + hold + HEAD + TAIL
            info = {"sp0": HEAD, "sp1": HEAD + vd, "T": T, "hold": hold}
            n = int(math.ceil(T * a.fps)); d = os.path.join(tmp, i); os.makedirs(d)
            jobs = [(fn, k / max(1, n - 1), k / a.fps, T, (k % 3) + 1, os.path.join(d, f"f{k:04d}.png"), info) for k in range(n)]
            with Pool() as pool: pool.map(draw_frame, jobs, chunksize=4)
            out = os.path.join(a.assets, f"{i}.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", os.path.join(d, "f%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
            shutil.rmtree(d); print(i, f"{n} frames, {T:.1f}s", flush=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("voices"); v.add_argument("scenes"); v.add_argument("assets")
    r = sub.add_parser("render"); r.add_argument("scenes"); r.add_argument("assets"); r.add_argument("--fps", type=int, default=12); r.add_argument("--only", nargs="*")
    a = ap.parse_args(); (cmd_voices if a.cmd == "voices" else cmd_render)(a)
