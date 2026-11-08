#!/usr/bin/env python3
"""Skip engine v2: real-cartoon rooms, anti-aliased 2x drawing, lip-sync, walk-ins, punch-in camera.
Same episode JSON as v1.  python3 skip2.py ep.json out.mp4
"""
import json, math, subprocess, sys
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import skip_v1 as v1

W, H, FPS, K = 1080, 1920, 24, 2
FLOOR = 1200          # feet line
WALL_END = 1010       # where floor starts
PANEL = 1270          # caption panel top
B = v1.B
def F(s): return ImageFont.truetype(B, s)
BLACK = (28, 24, 32); WHITE = (255, 255, 255)
ORANGE = (255, 132, 26); ORANGE_D = (220, 96, 10); BLUE = (52, 130, 240); BLUE_L = (120, 185, 255)
SKIN = (255, 255, 255)

# ---------- scaled drawing proxy (draw at 2x for anti-aliasing) ----------
def _sc(v, k):
    if isinstance(v, (int, float)): return v * k
    if isinstance(v, tuple) and len(v) == 2 and all(isinstance(q, (int, float)) for q in v): return (v[0] * k, v[1] * k)
    return [ _sc(q, k) for q in v ]
class SD:
    def __init__(s, d, k): s.d, s.k = d, k
    def _w(s, kw):
        if 'width' in kw: kw['width'] = max(1, int(round(kw['width'] * s.k)))
        if 'stroke_width' in kw: kw['stroke_width'] = int(kw['stroke_width'] * s.k)
        return kw
    def line(s, xy, **kw): s.d.line(_sc(xy, s.k), **s._w(kw))
    def ellipse(s, xy, **kw): s.d.ellipse(_sc(list(xy), s.k), **s._w(kw))
    def polygon(s, xy, **kw): s.d.polygon(_sc(list(xy), s.k), **s._w(kw))
    def rectangle(s, xy, **kw): s.d.rectangle(_sc(list(xy), s.k), **s._w(kw))
    def rounded_rectangle(s, xy, r=0, **kw): s.d.rounded_rectangle(_sc(list(xy), s.k), r * s.k, **s._w(kw))
    def arc(s, xy, a, b, **kw): s.d.arc(_sc(list(xy), s.k), a, b, **s._w(kw))
    def chord(s, xy, a, b, **kw): s.d.chord(_sc(list(xy), s.k), a, b, **s._w(kw))
    def pieslice(s, xy, a, b, **kw): s.d.pieslice(_sc(list(xy), s.k), a, b, **s._w(kw))
    def text(s, xy, txt, font=None, **kw):
        f = ImageFont.truetype(font.path, int(font.size * s.k)) if font else None
        s.d.text(_sc(xy, s.k), txt, font=f, **s._w(kw))
    def textlength(s, txt, font=None): return s.d.textlength(txt, font=font)

def ease(x): x = max(0., min(1., x)); return 1 - (1 - x) ** 3
def back(x):
    x = max(0., min(1., x)); c = 1.9; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

# ---------- rooms ----------
ROOM = {
    'kitchen': dict(wall=(178, 226, 210), wall2=(150, 208, 190), floor=(214, 170, 120), deco=['window', 'clock_wall', 'lamp']),
    'bedroom': dict(wall=(92, 96, 168), wall2=(70, 72, 140), floor=(160, 120, 90), deco=['frame', 'lamp_dim'], night=True),
    'living':  dict(wall=(250, 214, 160), wall2=(236, 190, 130), floor=(190, 140, 95), deco=['window', 'frame', 'lamp']),
    'door':    dict(wall=(206, 226, 250), wall2=(180, 206, 240), floor=(200, 156, 108), deco=['frame', 'lamp']),
    'desk':    dict(wall=(220, 210, 245), wall2=(196, 184, 232), floor=(190, 145, 100), deco=['window', 'shelf_wall', 'lamp']),
    'store':   dict(wall=(245, 245, 236), wall2=(225, 228, 214), floor=(210, 214, 220), deco=['sign'], tiles=True),
    'laundry': dict(wall=(200, 236, 246), wall2=(170, 220, 236), floor=(205, 205, 215), deco=['window', 'lamp'], tiles=True),
    'blank':   dict(wall=(255, 247, 228), wall2=(255, 236, 200), floor=None, deco=['burst']),
}
_cache = {}
def room_bg(name):
    if name in _cache: return _cache[name]
    R = ROOM.get(name, ROOM['blank'])
    im = Image.new('RGB', (W * K, H * K), WHITE); d0 = ImageDraw.Draw(im); d = SD(d0, K)
    # wall gradient + vertical stripes
    for y in range(0, WALL_END, 4):
        t = y / WALL_END; c = tuple(int(R['wall'][i] * (1 - t * .25) + R['wall2'][i] * t * .25) for i in range(3))
        d.rectangle([0, y, W, y + 4], fill=c)
    if name != 'blank':
        for x in range(0, W, 120): d.rectangle([x, 0, x + 60, WALL_END], fill=tuple(min(255, c + 6) for c in R['wall']))
        # crown + baseboard
        d.rectangle([0, 0, W, 26], fill=R['wall2']); d.rectangle([0, WALL_END - 34, W, WALL_END], fill=WHITE); d.line([(0, WALL_END - 34), (W, WALL_END - 34)], fill=(200, 200, 210), width=3)
    else:
        cx, cy = W / 2, 720
        for i in range(24):
            a0 = i * 2 * math.pi / 24; a1 = a0 + math.pi / 24
            d.polygon([(cx, cy), (cx + math.cos(a0) * 1600, cy + math.sin(a0) * 1600), (cx + math.cos(a1) * 1600, cy + math.sin(a1) * 1600)], fill=(255, 238, 205))
    # floor
    if R['floor']:
        fl = R['floor']
        d.rectangle([0, WALL_END, W, PANEL], fill=fl)
        if R.get('tiles'):
            for x in range(-600, W + 600, 130): d.line([(W / 2 + (x - W / 2) * .55, WALL_END), (x, PANEL)], fill=tuple(c - 22 for c in fl), width=3)
            for y in (1050, 1110, 1185): d.line([(0, y), (W, y)], fill=tuple(c - 22 for c in fl), width=3)
        else:
            for y in range(WALL_END + 40, PANEL, 52): d.line([(0, y), (W, y)], fill=tuple(c - 28 for c in fl), width=4)
            for i, y in enumerate(range(WALL_END, PANEL, 52)):
                for x in range((i * 170) % 340, W, 340): d.line([(x, y), (x, y + 52)], fill=tuple(c - 28 for c in fl), width=4)
        d.rectangle([0, WALL_END, W, WALL_END + 10], fill=tuple(c - 40 for c in fl))
    # deco
    night = R.get('night')
    for dc in R['deco']:
        if dc == 'window':
            x0, y0 = 90, 210; sky = (40, 46, 96) if night else (150, 210, 255)
            d.rounded_rectangle([x0 - 14, y0 - 14, x0 + 254, y0 + 314], 10, fill=WHITE, outline=BLACK, width=6)
            d.rectangle([x0, y0, x0 + 240, y0 + 300], fill=sky)
            if not night:
                d.ellipse([x0 + 150, y0 + 40, x0 + 210, y0 + 100], fill=(255, 230, 120))
                for cx, cy in ((x0 + 70, y0 + 120), (x0 + 120, y0 + 200)):
                    for dx, r in ((-30, 26), (0, 36), (32, 26)): d.ellipse([cx + dx - r, cy - r, cx + dx + r, cy + r], fill=WHITE)
                d.polygon([(x0, y0 + 300), (x0 + 80, y0 + 230), (x0 + 160, y0 + 270), (x0 + 240, y0 + 210), (x0 + 240, y0 + 300)], fill=(110, 190, 120))
            d.line([(x0 + 120, y0), (x0 + 120, y0 + 300)], fill=WHITE, width=8); d.line([(x0, y0 + 150), (x0 + 240, y0 + 150)], fill=WHITE, width=8)
            for side in (0, 1):  # curtains
                xx = x0 - 40 if side == 0 else x0 + 200
                d.polygon([(xx, y0 - 30), (xx + 80, y0 - 30), (xx + 60 if side == 0 else xx + 80, y0 + 330), (xx, y0 + 330) if side == 0 else (xx + 20, y0 + 330)], fill=(240, 110, 110), outline=BLACK, width=4)
            d.rectangle([x0 - 60, y0 - 40, x0 + 300, y0 - 26], fill=(120, 80, 50))
        elif dc == 'frame':
            d.rounded_rectangle([700, 230, 920, 420], 8, fill=(255, 250, 235), outline=(120, 80, 50), width=12)
            d.polygon([(730, 390), (790, 300), (840, 360), (870, 320), (900, 390)], fill=(110, 180, 120)); d.ellipse([850, 260, 885, 295], fill=(255, 200, 80))
        elif dc == 'clock_wall':
            d.ellipse([760, 180, 900, 320], fill=WHITE, outline=BLACK, width=8); d.line([(830, 250), (830, 200)], fill=BLACK, width=7); d.line([(830, 250), (868, 262)], fill=BLACK, width=7)
        elif dc in ('lamp', 'lamp_dim'):
            d.line([(540, 0), (540, 90)], fill=BLACK, width=5); d.chord([470, 60, 610, 170], 180, 360, fill=(255, 205, 80) if dc == 'lamp' else (190, 170, 120), outline=BLACK, width=5)
        elif dc == 'coat':
            d.rectangle([380, 300, 560, 318], fill=(120, 80, 50));
            for x in (410, 470, 530): d.ellipse([x - 10, 312, x + 10, 332], fill=BLACK)
            d.polygon([(400, 330), (450, 330), (470, 520), (380, 520)], fill=(90, 150, 90), outline=BLACK, width=4)
        elif dc == 'shelf_wall':
            d.rectangle([640, 300, 960, 318], fill=(120, 80, 50))
            for i, c in enumerate([(230, 90, 90), (90, 150, 230), (250, 200, 70), (120, 190, 120), (180, 120, 220)]): d.rectangle([660 + i * 55, 200 + (i % 2) * 20, 700 + i * 55, 300], fill=c, outline=BLACK, width=3)
        elif dc == 'sign':
            d.rounded_rectangle([300, 120, 780, 250], 20, fill=(230, 60, 60), outline=BLACK, width=6); d.text((540, 185), 'SALE!', font=F(90), fill=WHITE, anchor='mm')
    if night:
        ov = Image.new('RGBA', im.size, (20, 20, 60, 70)); im = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
    # caption panel
    d0 = ImageDraw.Draw(im); d = SD(d0, K)
    d.rectangle([0, PANEL, W, H], fill=(30, 28, 44))
    d.rectangle([0, PANEL, W, PANEL + 10], fill=(255, 196, 40))
    im = im.resize((W, H), Image.LANCZOS)
    _cache[name] = im
    return im

# ---------- Skip v2 ----------
def limb(d, a, b, bend, w=11, c=BLACK):
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
    e = (mx - dy / L * bend, my + dx / L * bend)
    d.line([a, e, b], fill=c, width=w, joint='curve')
    for p in (a, e): d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=c)

def skip2(d, x, y, b, t, lt, mouth_open):
    pose = b.get('pose', 'stand'); gray = b.get('gray', False)
    hoodie = (150, 150, 158) if gray else ORANGE; hoodie_d = (120, 120, 128) if gray else ORANGE_D
    hair = (140, 140, 150) if gray else BLUE; hair_l = (190, 190, 200) if gray else BLUE_L
    # squash & stretch on entrance
    pop = back(lt / .35); sq = 1 + (1 - min(1, lt / .35)) * .12 * math.sin(lt * 25)
    breathe = math.sin(t * 2.4) * 5
    shake = (math.sin(t * 60) * 6) if pose == 'panic' else 0
    x = x + shake
    # shadow
    d.ellipse([x - 120, y - 16, x + 120, y + 16], fill=(0, 0, 0, 60) if False else (0, 0, 0))
    hipy = y - 230 * sq; necky = y - 470 * sq - breathe; hx, hy = x, necky - 92 - breathe * .5
    tilt = {'think': -10, 'panic': 0, 'phone': 6, 'sleep': 14}.get(pose, math.sin(t * 1.7) * 3)
    hx += tilt * 1.5
    # legs
    if pose == 'walk' or b.get('_walking'):
        s = math.sin(t * 10) * 42
        limb(d, (x, hipy), (x - 25 + s, y), 14); limb(d, (x, hipy), (x + 25 - s, y), -14)
    else:
        limb(d, (x, hipy), (x - 48, y), 10); limb(d, (x, hipy), (x + 48, y), -10)
    for fx in ((x - 48, y), (x + 48, y)) if not (pose == 'walk' or b.get('_walking')) else ((x - 25 + math.sin(t * 10) * 42, y), (x + 25 - math.sin(t * 10) * 42, y)):
        d.ellipse([fx[0] - 26, fx[1] - 14, fx[0] + 30, fx[1] + 8], fill=BLACK)
    # hoodie body with hood + pocket + strings
    d.polygon([(x - 80, necky + 4), (x + 80, necky + 4), (x + 102, hipy + 24), (x - 102, hipy + 24)], fill=hoodie, outline=BLACK, width=7)
    d.rectangle([x - 102, hipy + 4, x + 102, hipy + 24], fill=hoodie_d, outline=BLACK, width=5)
    d.rounded_rectangle([x - 52, hipy - 78, x + 52, hipy - 18], 14, fill=hoodie_d, outline=BLACK, width=5)
    d.chord([x - 70, necky - 22, x + 70, necky + 40], 0, 180, fill=hoodie_d, outline=BLACK, width=5)
    for sx in (x - 22, x + 22): d.line([(sx, necky + 30), (sx + (sx - x) * .2, necky + 110)], fill=WHITE, width=5); d.ellipse([sx - 6 + (sx - x) * .2, necky + 106, sx + 6 + (sx - x) * .2, necky + 118], fill=WHITE)
    shl = (x - 72, necky + 34); shr = (x + 72, necky + 34)
    held = None; wave = math.sin(t * 6) * 10
    P = {
        'stand': ((x - 140, hipy + 30), (x + 140, hipy + 30), 30, -30),
        'walk': ((x - 140 + math.sin(t * 10) * 30, hipy + 30), (x + 140 - math.sin(t * 10) * 30, hipy + 30), 30, -30),
        'think': ((x - 140, hipy + 30), (hx + 30, hy + 60), 30, 60),
        'panic': ((hx - 95, hy - 40 + wave), (hx + 95, hy - 40 - wave), -50, 50),
        'thumbs': ((x - 140, hipy + 30), (x + 170, necky - 50 + wave * .5), 30, -40),
        'phone': ((x - 140, hipy + 30), (hx + 130, hy + 120), 30, 50),
        'point': ((x - 140, hipy + 30), (x + 260, necky + 10 + wave * .4), 30, -10),
        'hold': ((x - 160, hipy + 50), (x + 140, hipy + 30), 40, -30),
        'sleep': ((x - 140, hipy + 30), (x + 140, hipy + 30), 30, -30),
    }
    hl, hr, bl, br = P.get(pose, P['stand'])
    if pose == 'phone': held = 'phone'
    if pose == 'hold': held = b.get('holding', 'bag')
    limb(d, shl, hl, bl); limb(d, shr, hr, br)
    for h in (hl, hr): d.ellipse([h[0] - 19, h[1] - 19, h[0] + 19, h[1] + 19], fill=BLACK)
    if pose == 'thumbs': d.rounded_rectangle([hr[0] - 7, hr[1] - 46, hr[0] + 7, hr[1] - 10], 6, fill=BLACK)
    if held == 'phone':
        d.rounded_rectangle([hr[0] - 30, hr[1] - 92, hr[0] + 30, hr[1] + 4], 10, fill=(40, 40, 52)); d.rounded_rectangle([hr[0] - 23, hr[1] - 82, hr[0] + 23, hr[1] - 8], 6, fill=(110, 190, 255))
    elif held == 'bag':
        d.ellipse([hl[0] - 46, hl[1], hl[0] + 46, hl[1] + 100], fill=(30, 30, 34), outline=BLACK, width=3); d.polygon([(hl[0] - 14, hl[1] + 6), (hl[0] + 14, hl[1] + 6), (hl[0], hl[1] - 16)], fill=(30, 30, 34))
    elif held == 'keys':
        d.ellipse([hl[0] - 17, hl[1] + 6, hl[0] + 17, hl[1] + 40], outline=(230, 180, 40), width=8); d.rectangle([hl[0] - 5, hl[1] + 40, hl[0] + 5, hl[1] + 86], fill=(230, 180, 40))
    elif held == 'clothes':
        d.rounded_rectangle([hl[0] - 58, hl[1] - 12, hl[0] + 58, hl[1] + 80], 16, fill=(120, 190, 255), outline=BLACK, width=5)
    # head
    R = 92
    d.ellipse([hx - R, hy - R, hx + R, hy + R], fill=SKIN, outline=BLACK, width=8)
    d.ellipse([hx - R - 14, hy - 4, hx - R + 8, hy + 26], fill=SKIN, outline=BLACK, width=5); d.ellipse([hx + R - 8, hy - 4, hx + R + 14, hy + 26], fill=SKIN, outline=BLACK, width=5)
    pts = []; N = 9
    for i in range(N * 2 + 1):
        a = math.pi * (1.06 + 0.88 * i / (N * 2))
        if i % 2: L = R + 66 + (14 if N - 3 < i < N + 3 else 0) + math.sin(t * 7 + i) * 5
        else: L = R * 0.97 if i in (0, N * 2) else R + 14
        pts.append((hx + math.cos(a) * L, hy + 6 + math.sin(a) * L))
    pts.append((hx, hy - R * .72))
    d.polygon(pts, fill=hair, outline=BLACK, width=6)
    for i in range(1, N * 2, 2):
        a = math.pi * (1.06 + 0.88 * i / (N * 2))
        d.line([(hx + math.cos(a) * (R * .95), hy + 6 + math.sin(a) * (R * .95)), (hx + math.cos(a) * (R + 40), hy + 6 + math.sin(a) * (R + 40))], fill=hair_l, width=8)
    # cheeks
    for cx in (hx - 52, hx + 52): d.ellipse([cx - 18, hy + 20, cx + 18, hy + 40], fill=(255, 190, 190))
    eyes = b.get('eyes', 'normal'); blink = (t % 3.3) < .1 and eyes in ('normal', 'side', 'wide')
    brow = {'wide': -16, 'panic': -18, 'tired': 6, 'side': -4, 'spiral': -10, 'happy': -8}.get(eyes, -6)
    if pose == 'panic': brow = -20
    for side, ex in ((-1, hx - 34), (1, hx + 34)):
        ey = hy - 12
        ang = {'tired': 8, 'wide': -12}.get(eyes, -6) * side
        d.line([(ex - 20, ey - 32 + brow - ang * .5), (ex + 20, ey - 32 + brow + ang * .5)], fill=BLACK, width=7)
        if blink or eyes == 'happy':
            d.arc([ex - 18, ey - 10, ex + 18, ey + 16], 200, 340, fill=BLACK, width=7); continue
        rr = 26 if eyes == 'wide' else 19
        if eyes == 'tired':
            d.ellipse([ex - 18, ey - 14, ex + 18, ey + 18], fill=WHITE, outline=BLACK, width=5); d.chord([ex - 19, ey - 16, ex + 19, ey + 14], 180, 360, fill=(235, 225, 210), outline=BLACK, width=5); d.ellipse([ex - 7, ey + 2, ex + 7, ey + 14], fill=BLACK); continue
        d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=WHITE, outline=BLACK, width=6)
        if eyes == 'spiral':
            for k in range(3): d.arc([ex - rr + 5 + k * 5, ey - rr + 5 + k * 5, ex + rr - 5 - k * 5, ey + rr - 5 - k * 5], int(t * 500 + k * 90) % 360, int(t * 500 + k * 90 + 260) % 360, fill=BLACK, width=4)
        else:
            off = 10 if eyes == 'side' else math.sin(t * .9) * 3
            pr = 10 if eyes != 'wide' else 9
            d.ellipse([ex - pr + off, ey - pr, ex + pr + off, ey + pr], fill=BLACK); d.ellipse([ex - 4 + off + 3, ey - 6, ex + 2 + off + 3, ey], fill=WHITE)
    # mouth with lip sync
    m = b.get('mouth', 'smile'); my = hy + 44; op = mouth_open
    if op > .08:
        h = 8 + op * 34; w = 26 + op * 8
        d.ellipse([hx - w, my - h / 2, hx + w, my + h / 2 + 6], fill=(120, 30, 40), outline=BLACK, width=6)
        d.chord([hx - w * .7, my + h * .1, hx + w * .7, my + h / 2 + 4], 0, 180, fill=(240, 110, 120))
    elif m == 'smile': d.arc([hx - 30, my - 22, hx + 30, my + 12], 20, 160, fill=BLACK, width=7)
    elif m == 'grin': d.chord([hx - 34, my - 18, hx + 34, my + 26], 0, 180, fill=BLACK); d.chord([hx - 24, my + 4, hx + 24, my + 24], 0, 180, fill=(240, 110, 120))
    elif m == 'o': d.ellipse([hx - 14, my - 10, hx + 14, my + 18], fill=BLACK)
    elif m == 'frown': d.arc([hx - 28, my, hx + 28, my + 32], 200, 340, fill=BLACK, width=7)
    else: d.line([(hx - 24, my + 6), (hx + 24, my + 6)], fill=BLACK, width=7)
    if b.get('sweat') or pose == 'panic':
        for k, (sx, sy) in enumerate(((hx + 104, hy - 46), (hx - 110, hy - 24))):
            sy += (t * 120 + k * 40) % 60
            d.polygon([(sx, sy - 24), (sx - 13, sy + 6), (sx + 13, sy + 6)], fill=(110, 190, 255)); d.ellipse([sx - 13, sy - 6, sx + 13, sy + 20], fill=(110, 190, 255), outline=(60, 130, 210), width=2)
    if pose == 'panic':  # stress lines
        for k in range(3):
            a = -2.4 + k * .4; d.line([(hx + math.cos(a) * 150, hy + math.sin(a) * 150), (hx + math.cos(a) * 190, hy + math.sin(a) * 190)], fill=BLACK, width=6)
    if pose == 'sleep':
        for i, z in enumerate('Zzz'): d.text((hx + 120 + i * 38, hy - 100 - i * 42 + math.sin(t * 3 + i) * 8), z, font=F(54 + i * 8), fill=WHITE, stroke_width=4, stroke_fill=BLACK)
    if b.get('bubble'):
        bx, by = hx + 175, hy - 190; s = back((lt - .15) / .35)
        if s > 0:
            for k, (ox, oy, r) in enumerate(((-70, 150, 12), (-45, 115, 18))): d.ellipse([bx + ox - r, by + oy - r, bx + ox + r, by + oy + r], fill=WHITE, outline=BLACK, width=5)
            d.ellipse([bx - 100 * s, by - 78 * s, bx + 100 * s, by + 78 * s], fill=WHITE, outline=BLACK, width=6)
            v1.prop(d, b['bubble'], bx, by + 46 * s, .55 * s, t)

STATIC = {'kitchen': [('trash', 130, 1.0), ('kitchen', 770, 1.0)], 'bedroom': [('bed', 720, .9)], 'living': [('couch', 330, .9), ('tv', 860, 1.0)],
          'door': [('door', 880, 1.0), ('plant', 120, 1.0)], 'desk': [('desk', 790, 1.0), ('plant', 120, .9)], 'store': [('shelf', 790, 1.0)],
          'laundry': [('washer', 830, 1.0), ('basket', 130, 1.0)], 'blank': []}

def mouth_curve(audio, sr, n):
    hop = sr // FPS; env = np.array([np.sqrt((audio[i * hop:(i + 1) * hop] ** 2).mean() + 1e-12) for i in range(n)])
    env = env / (np.percentile(env, 95) + 1e-9); env = np.clip(env, 0, 1)
    out = np.zeros_like(env); a = 0
    for i, v in enumerate(env): a = a * .45 + v * .55; out[i] = a
    return np.where(out > .18, out, 0)

def outlined(d, xy, text, size, fill=WHITE, stroke=BLACK, sw=10):
    d.text(xy, text, font=F(size), fill=fill, anchor='mm', stroke_width=sw, stroke_fill=stroke)

def render_frame(b, prev_x, lt, gt, D, mo):
    if b.get('card'):
        im = Image.new('RGB', (W * K, H * K), (24, 24, 40)); d = SD(ImageDraw.Draw(im), K)
        s = back(lt / .4)
        for i in range(30):
            a = i * 2 * math.pi / 30 + gt * .3; d.line([(W / 2 + math.cos(a) * 300, 820 + math.sin(a) * 300), (W / 2 + math.cos(a) * 1400, 820 + math.sin(a) * 1400)], fill=(36, 36, 58), width=26)
        v1.prop(d, 'clock', W / 2, 820 + 200 * s, 2.3 * s, gt * 6)
        txt = b['card'].split('|'); outlined(d, (W / 2, 1150), txt[0], int(118 * s) or 1, fill=(255, 214, 40), stroke=(24, 24, 40), sw=0)
        if len(txt) > 1: outlined(d, (W / 2, 1275), txt[1], 74, stroke=(24, 24, 40), sw=0)
        return im.resize((W, H), Image.LANCZOS)
    st = b.get('set', 'blank'); bg = room_bg(st).copy()
    layer = Image.new('RGBA', (W * K, PANEL * K), (0, 0, 0, 0)); d = SD(ImageDraw.Draw(layer), K)
    for name, x, s in STATIC.get(st, []): v1.prop(d, name, x, FLOOR, s, gt)
    pp = ease(lt / .3)
    for p in b.get('props', []):
        name, x = p[0], p[1]; y = p[2] if len(p) > 2 else FLOOR; y = FLOOR if y >= 1239 else y
        s = (p[3] if len(p) > 3 else 1.0) * back(lt / .4)
        if s > .02: v1.prop(d, name, x, y - (1 - pp) * 40, s, gt)
    tx = b.get('x', 420); wk = ease(lt / .45)
    sx = prev_x + (tx - prev_x) * wk if prev_x is not None else tx
    bb = dict(b); bb['_walking'] = prev_x is not None and abs(tx - prev_x) > 30 and lt < .45
    sh = Image.new('RGBA', layer.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([(sx - 130) * K, (FLOOR - 18) * K, (sx + 130) * K, (FLOOR + 18) * K], fill=(0, 0, 0, 70))
    layer = Image.alpha_composite(sh, layer); d = SD(ImageDraw.Draw(layer), K)
    skip2(d, sx, FLOOR, bb, gt, lt, mo)
    if b.get('arrow'):
        ax, ay = b['arrow']; ay = min(ay, FLOOR - 40); p = math.sin(gt * 8) * 12
        d.polygon([(ax - 70 + p, ay - 22), (ax + p, ay - 22), (ax + p, ay - 48), (ax + 50 + p, ay), (ax + p, ay + 48), (ax + p, ay + 22), (ax - 70 + p, ay + 22)], fill=(235, 50, 50), outline=BLACK, width=5)
    layer = layer.resize((W, PANEL), Image.LANCZOS)
    # punch-in camera
    z = 1 + .035 * ease(lt / max(.5, D)) + (.02 if b.get('pose') == 'panic' else 0)
    scene = bg.crop((0, 0, W, PANEL)).convert('RGBA'); scene = Image.alpha_composite(scene, layer)
    if z > 1.001:
        cw, ch = int(W / z), int(PANEL / z); scene = scene.crop(((W - cw) // 2, (PANEL - ch) // 2 + 30, (W - cw) // 2 + cw, (PANEL - ch) // 2 + 30 + ch)).resize((W, PANEL), Image.BILINEAR)
    bg.paste(scene.convert('RGB'), (0, 0))
    d = ImageDraw.Draw(bg)
    if b.get('label'):
        lab = b['label']; f = F(84); tw = d.textlength(lab, font=f)
        col = (130, 130, 140) if lab.startswith('NON') else (235, 50, 50)
        d.rounded_rectangle([W / 2 - tw / 2 - 40, 130, W / 2 + tw / 2 + 40, 250], 30, fill=col, outline=BLACK, width=6)
        d.text((W / 2, 190), lab, font=f, fill=WHITE, anchor='mm', stroke_width=5, stroke_fill=BLACK)
    if b.get('counter'): v1.chip(d, W - 220, 290, b['counter'], 'yellow', 42, 400)
    y = PANEL + 70
    if b.get('cap'):
        sc = .7 + .3 * back(lt / .3)
        y = v1.chip(d, W / 2, y, b['cap'], b.get('chip', 'red'), max(20, int(66 * sc)))
    if b.get('cap2') and lt > .25: v1.chip(d, W / 2, y + 28, b['cap2'], b.get('chip2', 'dark'), 46)
    return bg

def build(ep, out):
    beats = ep['beats']
    segs, durs, sr = v1.tts([b['say'] for b in beats], None)
    voice = np.concatenate(segs); audio = voice.copy()
    t0 = 0
    for b, dd in zip(beats, durs):
        if b.get('sfx'):
            s = v1.sfx(b['sfx'], sr); i = int(t0 * sr); audio[i:i + len(s)] += s[:len(audio) - i]
        t0 += dd
    audio = audio / max(1e-6, np.abs(audio).max()) * .89
    wav = out + '.wav'; sf.write(wav, audio, sr)
    total = sum(durs); n = int(total * FPS); mo = mouth_curve(voice, sr, n)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', out], stdin=subprocess.PIPE)
    starts = np.cumsum([0] + durs[:-1]); bi = 0
    xs = [b.get('x', 420) if not b.get('card') else None for b in beats]
    for fi in range(n):
        gt = fi / FPS
        while bi + 1 < len(beats) and gt >= starts[bi + 1]: bi += 1
        prev = None
        if bi > 0 and xs[bi - 1] is not None and beats[bi - 1].get('set') == beats[bi].get('set'): prev = xs[bi - 1]
        p.stdin.write(render_frame(beats[bi], prev, gt - starts[bi], gt, durs[bi], float(mo[fi])).tobytes())
    p.stdin.close(); p.wait()
    print('TOTAL', round(total, 1))

if __name__ == '__main__':
    build(json.load(open(sys.argv[1])), sys.argv[2])
