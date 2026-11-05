#!/usr/bin/env python3
"""Short 2: The Keys (vertical). Reuses the vertical rig from short_thirsty/draw.py.
  draw.py voices SCENES ASSETS | draw.py render SCENES ASSETS [--fps 12] [--only s001 ...]"""
import math, os, sys, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "short_thirsty")); sys.path = [p for p in sys.path if not p.endswith("short_keys")]
import draw as V
from draw import (W, H, G, K, HIP, SEAT, stand, sit, F, room, sofa, kitchen, sink, title, ease, pose_at, walk, P, bubble, qmark, check, spiral, clock, plate, cup, phone,
                  sunrise_v, INK, GOLD, GOLDL, SKY, WALL, FLOOR, TEAL, PINK, PURP, YEL, GRN, BLUE, RED, ORANGE, CREAM, RAIN)
from anim_stick import ell

WOOD = (160, 110, 70); BAG = (40, 40, 48); SOCK = (120, 200, 120)


# ---------------------------------------------------------------- props
def door(c, x=120, hook=True, keys_on_hook=False):
    c.rect(x, 560, x + 330, G, fill=WOOD); c.rect(x + 30, 600, x + 300, 1000, fill=(190, 140, 95)); c.rect(x + 30, 1040, x + 300, G - 40, fill=(190, 140, 95))
    c.circ(x + 280, 1080, 14, fill=YEL)
    if hook:
        c.line([(x + 400, 760), (x + 400, 800), (x + 420, 820)], INK, 1.4)
        if keys_on_hook: keys(c, x + 418, 850)


def keys(c, x, y, s=1.0):
    c.circ(x, y, 16 * s, fill=None, w=1.3)
    for dx in (0, 14):
        c.line([(x + dx, y + 14 * s), (x + dx, y + 60 * s), (x + dx + 10 * s, y + 60 * s), (x + dx + 10 * s, y + 50 * s), (x + dx, y + 50 * s)], GOLD, 1.3)


def counter(c, x0=520, mail=True, mug=True, sock=True, lift=0.0):
    c.rect(x0, G - 260, W, G, fill=(205, 160, 112)); c.rect(x0, G - 290, W, G - 255, fill=(245, 238, 225))
    if sock: c.poly([(x0 + 240, G - 300), (x0 + 330, G - 300), (x0 + 330, G - 330), (x0 + 360, G - 330), (x0 + 360, G - 390), (x0 + 300, G - 390), (x0 + 300, G - 330), (x0 + 240, G - 330)], SOCK)
    if mug: c.rect(x0 + 420, G - 380, x0 + 500, G - 292, fill=RED); c.line([(x0 + 500, G - 365), (x0 + 530, G - 360), (x0 + 530, G - 320), (x0 + 500, G - 315)], INK, .9)
    if mail:
        for i in range(5):
            y = G - 300 - i * 16 - lift * 180; c.poly([(x0 + 120 + i * 6, y), (x0 + 340 + i * 6, y - 8), (x0 + 345 + i * 6, y - 64), (x0 + 125 + i * 6, y - 56)], (250, 246, 236) if i % 2 else (230, 225, 240))


def one_plate_sink(c):
    c.rect(300, G - 320, 780, G - 255, fill=(120, 170, 215)); c.line([(800, G - 290), (800, G - 450), (720, G - 470)], INK, 1.6); plate(c, 540, G - 330, 1.0, CREAM)


def trash_bag(c, x, y, s=1.0, rip=0.0):
    ell(c, x, y - 90 * s, 90 * s, 110 * s, BAG)
    c.line([(x - 30 * s, y - 200 * s), (x, y - 230 * s), (x + 30 * s, y - 200 * s)], INK, 1.2)
    if rip > 0:
        c.poly([(x - 60 * s, y - 60 * s), (x - 10 * s, y - 120 * s * rip), (x + 30 * s, y - 50 * s), (x + 70 * s, y - 100 * s * rip)], (236, 214, 178), False)


def trash_bits(c, x, y, spread, n=7, t=0.0):
    for i in range(n):
        a = i * 0.9; dx = math.cos(a) * spread * (0.4 + i / n); dy = min(0, -spread * 0.3 * math.sin(a * 2)) * (1 - spread / 400)
        col = RAIN[i % 7]
        if i % 3 == 0: c.circ(x + dx, G - 28 + dy, 26, fill=col)
        elif i % 3 == 1: c.poly([(x + dx - 36, G - 10 + dy), (x + dx + 36, G - 20 + dy), (x + dx + 28, G - 64 + dy), (x + dx - 30, G - 58 + dy)], col)
        else: c.rect(x + dx - 20, G - 84 + dy, x + dx + 20, G - 10 + dy, fill=col)


def window_car(c):
    c.rect(600, 500, 1000, 900, fill=SKY); c.rect(600, 760, 1000, 900, fill=(120, 170, 110), outline=False); c.line([(600, 760), (1000, 760)])
    c.rect(680, 720, 940, 800, fill=BLUE); c.poly([(720, 720), (760, 660), (880, 660), (920, 720)], (120, 190, 255))
    for x in (720, 900): c.circ(x, 805, 26, fill=INK, outline=False)
    c.line([(600, 500), (600, 900), (1000, 900), (1000, 500), (600, 500)]); c.line([(800, 500), (800, 900)])


def broom(c, hand, s=1.0, swing=0.0):
    tip = (hand[0] + 180 * s + swing, G - 10); c.line([hand, tip], (200, 160, 90), 1.4)
    for i in range(6): c.line([(tip[0] - 20 + i * 8 - 30, tip[1] - 60), (tip[0] - 50 + i * 12, tip[1])], YEL, 1.0)


def bowl(c, x, y, s=1.0, with_keys=False):
    ell(c, x, y, 90 * s, 28 * s, (220, 180, 90)); c.poly([(x - 90 * s, y), (x + 90 * s, y), (x + 60 * s, y + 70 * s), (x - 60 * s, y + 70 * s)], (200, 150, 62))
    if with_keys: keys(c, x - 10, y - 30, .8)


def stool(c, x): c.rect(x, G - 240, x + 240, G - 200, fill=WOOD); c.line([(x + 20, G - 200), (x + 20, G)]); c.line([(x + 220, G - 200), (x + 220, G)])


# ---------------------------------------------------------------- scenes
def s01(c, p, t, T):  # door, empty hook, patting pockets
    room(c, window=False); door(c)
    w = math.sin(t * 14)
    Z = stand(760, mood="worry", ra1=50 + 20 * w, ra2=120 + 20 * w, la1=-50 - 20 * w, la2=-120 - 20 * w, look=math.sin(t * 5), tilt=6 * math.sin(t * 5))
    F(c, Z, face=-1)
    title(c, "POV: leaving in 5", 540, 260, 92); title(c, "where are my keys", 540, 400, 72, bg=(255, 255, 255))


def s02(c, p, t, T):  # not on hook, walk to counter
    room(c, window=False); door(c); counter(c)
    keys_ = [(0, stand(700, mood="flat")), (.35, stand(700, mood="flat", ra1=-80, ra2=-130)), (.5, stand(700, mood="flat")), (1, stand(420, mood="open"))]
    Z = pose_at(keys_, p)
    if p > .5: Z = walk(Z, t, 1.0, 10)
    F(c, Z, face=-1 if p < .5 else 1)


def s03(c, p, t, T):  # lifts mail, sock revealed
    kitchen(c); counter(c, lift=ease((p - .3) / .3))
    Z = stand(420, mood="flat", ra1=60 + 40 * ease((p - .3) / .3), ra2=110, lean=5); F(c, Z)


def s04(c, p, t, T):  # holds sock up
    kitchen(c); counter(c, sock=False, lift=1)
    f = F(c, stand(420, mood="flat", ra1=150, ra2=175, tilt=-8))
    sx, sy = f["rh"]; c.poly([(sx - 30, sy), (sx + 30, sy), (sx + 30, sy + 90), (sx + 70, sy + 90), (sx + 70, sy + 130), (sx - 30, sy + 130)], SOCK)
    s = ease((p - .3) / .1)
    if s > .05: qmark(c, sx + 150, sy - 80, 1.6 * s, PURP)


def s05(c, p, t, T):  # sink, one plate (no figure)
    kitchen(c); one_plate_sink(c)
    for i in range(3):
        s = ease((p - .2 - i * .2) / .1) * (1 - ease((p - .5 - i * .2) / .1))
        if s > .05: c.circ(540 + i * 60 - 60, G - 420 - i * 40, 18 * s + 8, fill=(200, 230, 255))
    title(c, "just one plate", 540, 300, 80, bg=(255, 255, 255))


def s06(c, p, t, T):  # grabs trash bag
    kitchen(c); one_plate_sink(c)
    keys_ = [(0, stand(360, mood="open", ra1=60, ra2=100)), (.5, stand(360, mood="worry", ra1=40, ra2=60, lean=10)), (1, stand(360, mood="worry", ra1=30, ra2=40, lean=4))]
    f = F(c, pose_at(keys_, p)); trash_bag(c, f["rh"][0] + 110, G, 1.7)


def s07(c, p, t, T):  # bag rips, trash on floor
    kitchen(c); one_plate_sink(c)
    rip = ease((p - .15) / .2)
    f = F(c, stand(360, mood="tired" if p > .4 else "worry", ra1=30, ra2=40, lean=4, tilt=6 * rip)); trash_bag(c, f["rh"][0] + 110, G, 1.7, rip)
    if rip > 0: trash_bits(c, f["rh"][0] + 110, G, 80 + 360 * rip, t=t)


def s08(c, p, t, T):  # the car
    room(c, window=False); window_car(c); door(c); trash_bits(c, 300, G, 300)
    keys_ = [(0, stand(430, mood="tired", tilt=0)), (.3, stand(430, mood="open", tilt=10, look=1.5)), (.7, stand(430, mood="worry", tilt=10, look=1.5)), (1, stand(430, mood="worry", tilt=-8, look=-1))]
    F(c, pose_at(keys_, p))


def s09(c, p, t, T):  # abstract: one hour later
    c.rect(0, 0, W, H, fill=(50, 34, 100), outline=False)
    spiral(c, 540, 900, 440, 4.5, t * 1.4, 2.2); clock(c, 540, 900, 230, t * 560, t * 47)
    for i, kind in enumerate(("keys", "sock", "bag", "x")):
        a = t * 1.1 + i * math.pi / 2; x, y = 540 + 380 * math.cos(a), 900 + 520 * math.sin(a)
        if kind == "keys": keys(c, x, y, 1.2)
        elif kind == "sock": c.poly([(x - 30, y), (x + 30, y), (x + 30, y + 70), (x + 60, y + 70), (x + 60, y + 110), (x - 30, y + 110)], SOCK)
        elif kind == "bag": trash_bag(c, x, y + 100, .6)
        else: qmark(c, x, y - 10, 1.0, YEL)
    title(c, "1 hour later", 540, 300, 96, col=(255, 255, 255), bg=RED)


def s10(c, p, t, T):  # sweeping, then keys from pocket
    room(c, window=False); door(c); trash_bits(c, 330, G, 200)
    if p < .55:
        sw = 40 * math.sin(t * 7); f = F(c, stand(620, mood="tired", ra1=60 + 8 * math.sin(t * 7), ra2=95, lean=10)); broom(c, f["rh"], 1.0, sw)
    else:
        u = ease((p - .55) / .2)
        f = F(c, stand(620, mood="tired" if p < .85 else "open", ra1=40 + 110 * u, ra2=60 + 100 * u, tilt=8 * u)); keys(c, f["rh"][0] + 10, f["rh"][1] + 10, 1.2)
        s = ease((p - .8) / .1)
        if s > .05: title(c, "...", f["head"][0] + 170, f["head"][1] - 120, int(90 * s), bg=(255, 255, 255))


def s11(c, p, t, T):  # to camera
    room(c, wall=(214, 190, 255), floor=(150, 110, 200), window=False)
    f = F(c, stand(540, mood="smile", ra1=20, ra2=30, la1=-20, la2=-30, tilt=3 * math.sin(t * 3)))
    s = ease((p - .25) / .12)
    if s > .05: title(c, "if that's you too", 540, 300, int(84 * s), bg=PINK)


def s12(c, p, t, T):  # keys into the bowl by the door
    room(c, window=False); door(c); stool(c, 520); bowl(c, 640, G - 300, 1.0, with_keys=p > .45)
    keys_ = [(0, stand(900, mood="smile", ra1=20, ra2=30)), (.3, stand(900, mood="smile", ra1=90, ra2=120, lean=6)), (.45, stand(900, mood="smile", ra1=80, ra2=110, lean=6)), (1, stand(900, mood="smile", ra1=20, ra2=30))]
    Z = pose_at(keys_, p); f = F(c, Z, face=-1)
    if p < .45:
        u = ease((p - .25) / .2); keys(c, f["rh"][0] - 10, f["rh"][1] + 10, 1.2)
    s = ease((p - .55) / .1)
    if s > .05: check(c, 880, 640, 1.6 * s); title(c, "ONE spot", 540, 300, int(100 * s), bg=GRN)


def s13(c, p, t, T): sunrise_v(c, .3 + .6 * p, t, p); title(c, "Psalm 46:10", 540, 240, 88, bg=(255, 255, 255))


def s14(c, p, t, T):  # loop: door, keys in bowl, calm
    room(c, window=False); door(c); stool(c, 520); bowl(c, 640, G - 300, 1.0, with_keys=True)
    c.glow(540, 700, 320, col=GOLD, strength=150)
    F(c, stand(900, mood="smile", ra1=20, ra2=30, la1=-10, la2=-20), face=-1)
    s = ease((p - .4) / .12)
    if s > .05: title(c, "Keys get one place.", 540, 300, int(78 * s), bg=(255, 255, 255)); title(c, "The car can wait.", 540, 430, int(78 * s), bg=YEL)


RECIPES = {f"s{i:03d}": fn for i, fn in enumerate((s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12, s14), 1)}
V.RECIPES = RECIPES

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("voices"); v.add_argument("scenes"); v.add_argument("assets"); v.add_argument("--voice", default="am_michael"); v.add_argument("--speed", type=float, default=1.0)
    r = sub.add_parser("render"); r.add_argument("scenes"); r.add_argument("assets"); r.add_argument("--fps", type=int, default=12); r.add_argument("--only", nargs="*")
    a = ap.parse_args(); (V.cmd_voices if a.cmd == "voices" else V.cmd_render)(a)
