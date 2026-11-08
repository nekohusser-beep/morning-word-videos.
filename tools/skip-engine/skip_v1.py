#!/usr/bin/env python3
"""Skip ADHD engine: script JSON -> narrated 1080x1920 MP4 in the Skip #1 style.
Usage: python3 skip.py episode.json out.mp4
Beat keys: say, label, cap, chip(red|purple|dark|yellow), set(kitchen|bedroom|living|door|desk|store|laundry|blank),
props[list], pose(stand|think|panic|thumbs|phone|hold|walk|sleep|point), eyes(normal|wide|side|happy|tired|spiral),
mouth(smile|o|flat|frown|grin), counter "text", arrow [x,y], gray(bool non-ADHD Skip), sweat(bool), card "big text"
"""
import json, math, random, subprocess, sys, wave
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 24
B = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
def F(s): return ImageFont.truetype(B, s)
BLACK = (20, 20, 20); WHITE = (255, 255, 255); ORANGE = (255, 128, 20); BLUE = (40, 120, 230)
GRAYH = (130, 130, 130); WOOD = (205, 160, 110); WOODD = (150, 110, 70); STEEL = (110, 115, 125)
CHIP = {'red': (225, 45, 45), 'purple': (125, 70, 220), 'dark': (45, 45, 50), 'yellow': (255, 214, 40), 'green': (40, 170, 90)}
FLOOR = 1240

# ---------------- audio ----------------
def tts(lines, out_wav):
    from kokoro_onnx import Kokoro
    k = Kokoro('/home/claude/models/kokoro-v1.0.onnx', '/home/claude/models/voices-v1.0.bin')
    v = 0.6 * k.get_voice_style('am_onyx') + 0.4 * k.get_voice_style('am_michael')
    segs, durs = [], []
    for t in lines:
        a, sr = k.create(t, voice=v, speed=1.0, lang='en-us')
        a = np.concatenate([a.astype(np.float32), np.zeros(int(sr * 0.25), np.float32)])
        segs.append(a); durs.append(len(a) / sr)
    return segs, durs, sr

def sfx(kind, sr):
    t = np.arange(int(sr * {'pop': .12, 'whoosh': .35, 'buzz': .5, 'ding': .6, 'boing': .4}[kind])) / sr
    if kind == 'pop': x = np.sin(2 * np.pi * (500 + 1500 * t / t[-1]) * t) * np.exp(-t * 35)
    elif kind == 'whoosh': x = np.random.randn(len(t)) * np.sin(np.pi * t / t[-1]) * .4; x = np.convolve(x, np.ones(30) / 30, 'same')
    elif kind == 'buzz': x = np.sign(np.sin(2 * np.pi * 160 * t)) * ((t * 8) % 1 < .6) * .25
    elif kind == 'ding': x = (np.sin(2 * np.pi * 1320 * t) + .5 * np.sin(2 * np.pi * 1980 * t)) * np.exp(-t * 6) * .4
    else: x = np.sin(2 * np.pi * (220 + 180 * np.sin(t * 30)) * t) * np.exp(-t * 6) * .5
    return (x * .35).astype(np.float32)

# ---------------- drawing ----------------
def line(d, a, b, w=9, c=BLACK): d.line([a, b], fill=c, width=w); d.ellipse([b[0]-w/2, b[1]-w/2, b[0]+w/2, b[1]+w/2], fill=c)

def skip(d, x, y, b, t):
    """x,y = feet center on floor. b = beat dict."""
    pose = b.get('pose', 'stand'); gray = b.get('gray', False)
    bob = math.sin(t * 5) * 4 if pose not in ('sleep',) else 0
    hip = (x, y - 230 + bob); neck = (x, y - 470 + bob); hx, hy = x, y - 560 + bob; R = 85
    # legs
    if pose == 'walk':
        s = math.sin(t * 9) * 45
        line(d, hip, (x - 30 + s, y)); line(d, hip, (x + 30 - s, y))
    else:
        line(d, hip, (x - 45, y)); line(d, hip, (x + 45, y))
    # hoodie
    body = GRAYH if gray else ORANGE
    d.polygon([(x - 75, neck[1] + 5), (x + 75, neck[1] + 5), (x + 95, hip[1] + 20), (x - 95, hip[1] + 20)], fill=body, outline=BLACK, width=6)
    d.line([(x, neck[1] + 30), (x, hip[1] - 20)], fill=BLACK, width=4)
    d.rounded_rectangle([x - 45, hip[1] - 70, x + 45, hip[1] - 25], 10, outline=BLACK, width=4)
    sh_l = (x - 70, neck[1] + 30); sh_r = (x + 70, neck[1] + 30)
    # arms by pose
    held = None
    if pose in ('stand', 'walk', 'sleep'):
        sw = math.sin(t * 9) * 30 if pose == 'walk' else 0
        hl = (x - 130 + sw, hip[1] + 20); hr = (x + 130 - sw, hip[1] + 20)
    elif pose == 'think':
        hl = (x - 130, hip[1] + 20); hr = (x + 40, y - 520 + bob)
    elif pose == 'panic':
        hl = (x - 90, y - 640 + bob); hr = (x + 90, y - 640 + bob)
    elif pose == 'thumbs':
        hl = (x - 130, hip[1] + 20); hr = (x + 150, neck[1] - 40)
    elif pose == 'phone':
        hl = (x - 130, hip[1] + 20); hr = (x + 150, y - 470 + bob); held = 'phone'
    elif pose == 'point':
        hl = (x - 130, hip[1] + 20); hr = (x + 230, neck[1] + 10)
    elif pose == 'hold':
        hl = (x - 150, hip[1] + 40); hr = (x + 130, hip[1] + 20); held = b.get('holding', 'bag')
    else:
        hl = (x - 130, hip[1] + 20); hr = (x + 130, hip[1] + 20)
    line(d, sh_l, hl); line(d, sh_r, hr)
    for h in (hl, hr): d.ellipse([h[0] - 16, h[1] - 16, h[0] + 16, h[1] + 16], fill=BLACK)
    if held == 'phone':
        d.rounded_rectangle([hr[0] - 25, hr[1] - 75, hr[0] + 25, hr[1] + 5], 8, fill=(40, 40, 50)); d.rectangle([hr[0] - 18, hr[1] - 65, hr[0] + 18, hr[1] - 5], fill=(90, 170, 255))
    elif held == 'bag':
        d.ellipse([hl[0] - 40, hl[1], hl[0] + 40, hl[1] + 90], fill=(25, 25, 25)); d.polygon([(hl[0] - 12, hl[1] + 5), (hl[0] + 12, hl[1] + 5), (hl[0], hl[1] - 15)], fill=(25, 25, 25))
    elif held == 'keys':
        d.ellipse([hl[0] - 15, hl[1] + 5, hl[0] + 15, hl[1] + 35], outline=(200, 160, 30), width=6); d.rectangle([hl[0] - 4, hl[1] + 35, hl[0] + 4, hl[1] + 75], fill=(200, 160, 30))
    elif held == 'clothes':
        d.rounded_rectangle([hl[0] - 50, hl[1] - 10, hl[0] + 50, hl[1] + 70], 12, fill=(120, 190, 255), outline=BLACK, width=4)
    # head
    d.ellipse([hx - R, hy - R, hx + R, hy + R], fill=WHITE, outline=BLACK, width=7)
    hair = GRAYH if gray else BLUE
    for i in range(9):
        a = math.pi * (1.05 + i * 0.11); bx = hx + math.cos(a) * R * .9; by = hy + math.sin(a) * R * .9
        tx = hx + math.cos(a) * (R + 55 + (i % 2) * 18); ty = hy + math.sin(a) * (R + 55 + (i % 2) * 18)
        lx = hx + math.cos(a - .09) * R * .95; ly = hy + math.sin(a - .09) * R * .95
        rx = hx + math.cos(a + .09) * R * .95; ry = hy + math.sin(a + .09) * R * .95
        d.polygon([(lx, ly), (tx, ty), (rx, ry)], fill=hair, outline=BLACK)
    # eyes
    eyes = b.get('eyes', 'normal'); blink = (t % 3.1) < .12 and eyes in ('normal', 'side')
    for ex in (hx - 30, hx + 30):
        ey = hy - 10
        if blink or eyes == 'happy': d.arc([ex - 16, ey - 10, ex + 16, ey + 14], 200, 340, fill=BLACK, width=6); continue
        if eyes == 'tired':
            d.ellipse([ex - 16, ey - 12, ex + 16, ey + 16], fill=WHITE, outline=BLACK, width=4); d.rectangle([ex - 18, ey - 14, ex + 18, ey + 2], fill=WHITE); d.line([(ex - 17, ey + 2), (ex + 17, ey + 2)], fill=BLACK, width=5); d.ellipse([ex - 6, ey + 3, ex + 6, ey + 13], fill=BLACK); continue
        rr = 24 if eyes == 'wide' else 17
        d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=WHITE, outline=BLACK, width=5)
        if eyes == 'spiral':
            for k in range(3): d.arc([ex - rr + 5 + k * 5, ey - rr + 5 + k * 5, ex + rr - 5 - k * 5, ey + rr - 5 - k * 5], int(t * 400 + k * 90) % 360, int(t * 400 + k * 90 + 270) % 360, fill=BLACK, width=3)
        else:
            off = 9 if eyes == 'side' else 0
            d.ellipse([ex - 8 + off, ey - 8, ex + 8 + off, ey + 8], fill=BLACK)
    m = b.get('mouth', 'smile'); my = hy + 38
    if m == 'smile': d.arc([hx - 28, my - 20, hx + 28, my + 12], 20, 160, fill=BLACK, width=6)
    elif m == 'grin': d.chord([hx - 32, my - 18, hx + 32, my + 22], 0, 180, fill=BLACK)
    elif m == 'o': d.ellipse([hx - 13, my - 10, hx + 13, my + 16], fill=BLACK)
    elif m == 'frown': d.arc([hx - 26, my, hx + 26, my + 30], 200, 340, fill=BLACK, width=6)
    else: d.line([(hx - 22, my + 6), (hx + 22, my + 6)], fill=BLACK, width=6)
    if b.get('sweat'):
        for sx, sy in ((hx + 95, hy - 40), (hx - 100, hy - 20)):
            d.polygon([(sx, sy - 22), (sx - 12, sy + 6), (sx + 12, sy + 6)], fill=(90, 180, 255)); d.ellipse([sx - 12, sy - 6, sx + 12, sy + 18], fill=(90, 180, 255))
    if pose == 'sleep':
        for i, z in enumerate('Zzz'):
            d.text((hx + 110 + i * 35, hy - 90 - i * 40 + math.sin(t * 3 + i) * 8), z, font=F(50 + i * 8), fill=BLACK)
    if b.get('bubble'):
        bx, by = hx + 150, hy - 170
        d.ellipse([bx - 20, by + 90, bx, by + 110], outline=BLACK, width=4)
        d.ellipse([bx - 95, by - 70, bx + 95, by + 70], fill=WHITE, outline=BLACK, width=5)
        prop(d, b['bubble'], bx, by + 40, .55, t)

def prop(d, name, x, y, s, t):
    """draw prop with base at (x,y)."""
    S = lambda v: v * s
    if name == 'cup':
        d.polygon([(x - S(40), y - S(120)), (x + S(40), y - S(120)), (x + S(30), y), (x - S(30), y)], fill=(180, 225, 255), outline=BLACK, width=5)
        d.rectangle([x - S(34), y - S(80), x + S(34), y - S(5)], fill=(60, 150, 240))
    elif name == 'phone':
        sh = math.sin(t * 40) * 6 if (t % 1.2) < .5 else 0
        d.rounded_rectangle([x - S(55) + sh, y - S(190), x + S(55) + sh, y], 18, fill=(40, 40, 50)); d.rectangle([x - S(45) + sh, y - S(175), x + S(45) + sh, y - S(20)], fill=(90, 170, 255))
        for k in range(3): d.arc([x + S(60) + sh - k * 15, y - S(150) - k * 15, x + S(90) + sh + k * 15, y - S(90) + k * 15], 300, 60, fill=(225, 45, 45), width=5)
    elif name == 'keys':
        d.ellipse([x - S(30), y - S(140), x + S(30), y - S(80)], outline=(200, 160, 30), width=10); d.rectangle([x - S(8), y - S(85), x + S(8), y], fill=(200, 160, 30)); d.rectangle([x, y - S(30), x + S(25), y - S(15)], fill=(200, 160, 30))
    elif name == 'wallet':
        d.rounded_rectangle([x - S(70), y - S(90), x + S(70), y], 12, fill=(110, 70, 40), outline=BLACK, width=5); d.line([(x - S(70), y - S(55)), (x + S(70), y - S(55))], fill=BLACK, width=4)
    elif name == 'door':
        d.rectangle([x - S(110), y - S(520), x + S(110), y], fill=WOOD, outline=BLACK, width=7); d.ellipse([x + S(60), y - S(280), x + S(85), y - S(255)], fill=(230, 190, 40), outline=BLACK, width=3)
        d.rectangle([x - S(80), y - S(480), x + S(80), y - S(320)], outline=WOODD, width=5); d.rectangle([x - S(80), y - S(220), x + S(80), y - S(40)], outline=WOODD, width=5)
    elif name == 'bed':
        d.rectangle([x - S(260), y - S(140), x + S(260), y - S(60)], fill=(120, 160, 230), outline=BLACK, width=6); d.rectangle([x - S(280), y - S(260), x - S(240), y], fill=WOODD, outline=BLACK, width=5)
        d.rectangle([x + S(240), y - S(160), x + S(280), y], fill=WOODD, outline=BLACK, width=5); d.rounded_rectangle([x - S(235), y - S(190), x - S(120), y - S(140)], 20, fill=WHITE, outline=BLACK, width=5)
    elif name == 'moon':
        d.ellipse([x - S(60), y - S(120), x + S(60), y], fill=(250, 225, 120)); d.ellipse([x - S(20), y - S(135), x + S(85), y - S(25)], fill=(35, 40, 80))
    elif name == 'window_night':
        d.rectangle([x - S(130), y - S(260), x + S(130), y], fill=(35, 40, 80), outline=BLACK, width=7); prop(d, 'moon', x + S(30), y - S(90), s * .8, t); d.line([(x, y - S(260)), (x, y)], fill=BLACK, width=5)
    elif name == 'laptop':
        d.polygon([(x - S(130), y - S(190)), (x + S(130), y - S(190)), (x + S(120), y - S(20)), (x - S(120), y - S(20))], fill=(60, 65, 75), outline=BLACK); d.rectangle([x - S(110), y - S(175), x + S(110), y - S(35)], fill=(200, 230, 255))
        d.polygon([(x - S(160), y - S(20)), (x + S(160), y - S(20)), (x + S(180), y), (x - S(180), y)], fill=(90, 95, 105), outline=BLACK)
    elif name == 'desk':
        d.rectangle([x - S(260), y - S(300), x + S(260), y - S(270)], fill=WOOD, outline=BLACK, width=6); d.rectangle([x - S(240), y - S(270), x - S(210), y], fill=WOODD); d.rectangle([x + S(210), y - S(270), x + S(240), y], fill=WOODD)
    elif name == 'washer':
        d.rounded_rectangle([x - S(140), y - S(320), x + S(140), y], 18, fill=(235, 238, 242), outline=BLACK, width=7); d.ellipse([x - S(90), y - S(240), x + S(90), y - S(60)], fill=(160, 200, 240), outline=BLACK, width=7)
        d.rectangle([x - S(110), y - S(300), x + S(110), y - S(270)], fill=(200, 205, 212)); d.ellipse([x + S(70), y - S(298), x + S(95), y - S(273)], fill=(225, 45, 45))
    elif name == 'basket':
        d.polygon([(x - S(110), y - S(150)), (x + S(110), y - S(150)), (x + S(85), y), (x - S(85), y)], fill=(230, 200, 140), outline=BLACK, width=6)
        for k in range(3): d.ellipse([x - S(90) + k * S(55), y - S(210), x - S(20) + k * S(55), y - S(140)], fill=[(120, 190, 255), (255, 120, 150), (140, 220, 140)][k], outline=BLACK, width=4)
    elif name == 'couch':
        d.rounded_rectangle([x - S(260), y - S(260), x + S(260), y - S(120)], 30, fill=(150, 90, 200), outline=BLACK, width=6); d.rounded_rectangle([x - S(280), y - S(150), x + S(280), y - S(40)], 25, fill=(170, 110, 220), outline=BLACK, width=6)
        d.rectangle([x - S(250), y - S(40), x - S(220), y], fill=BLACK); d.rectangle([x + S(220), y - S(40), x + S(250), y], fill=BLACK)
    elif name == 'tv':
        d.rectangle([x - S(170), y - S(330), x + S(170), y - S(120)], fill=(30, 30, 40), outline=BLACK, width=6); d.rectangle([x - S(150), y - S(310), x + S(150), y - S(140)], fill=[(255, 120, 120), (120, 200, 255), (255, 220, 100)][int(t * 2) % 3])
        d.rectangle([x - S(15), y - S(120), x + S(15), y - S(40)], fill=BLACK); d.rectangle([x - S(80), y - S(40), x + S(80), y - S(25)], fill=BLACK)
    elif name == 'shelf':
        for k in range(3):
            yy = y - S(110) * k - S(40)
            d.rectangle([x - S(220), yy, x + S(220), yy + S(15)], fill=WOODD)
            for j in range(5): d.rectangle([x - S(200) + j * S(85), yy - S(80), x - S(140) + j * S(85), yy], fill=[(255, 120, 80), (90, 200, 120), (255, 210, 60), (120, 160, 255), (230, 120, 220)][(j + k) % 5], outline=BLACK, width=3)
    elif name == 'cart':
        d.polygon([(x - S(150), y - S(230)), (x + S(130), y - S(230)), (x + S(100), y - S(80)), (x - S(120), y - S(80))], outline=BLACK, fill=(220, 225, 230), width=7); d.line([(x - S(150), y - S(230)), (x - S(200), y - S(280))], fill=BLACK, width=8)
        for cx in (x - S(90), x + S(70)): d.ellipse([cx - S(22), y - S(45), cx + S(22), y], fill=BLACK)
    elif name == 'list':
        d.rectangle([x - S(80), y - S(220), x + S(80), y], fill=(255, 250, 200), outline=BLACK, width=5)
        for k in range(5): d.line([(x - S(55), y - S(185) + k * S(38)), (x + S(55), y - S(185) + k * S(38))], fill=(120, 120, 140), width=5)
    elif name == 'milk':
        d.polygon([(x - S(50), y - S(170)), (x + S(50), y - S(170)), (x + S(50), y), (x - S(50), y)], fill=WHITE, outline=BLACK, width=5); d.polygon([(x - S(50), y - S(170)), (x, y - S(230)), (x + S(50), y - S(170))], fill=(90, 150, 230), outline=BLACK); d.rectangle([x - S(35), y - S(120), x + S(35), y - S(60)], fill=(90, 150, 230))
    elif name == 'kitchen':
        d.rectangle([x - S(260), y - S(300), x + S(260), y], fill=WOOD, outline=BLACK, width=6); d.line([(x, y - S(300)), (x, y)], fill=WOODD, width=5)
        d.rectangle([x - S(275), y - S(320), x + S(275), y - S(295)], fill=(110, 110, 115)); d.rectangle([x - S(260), y - S(700), x + S(260), y - S(470)], fill=WOOD, outline=BLACK, width=6); d.line([(x, y - S(700)), (x, y - S(470))], fill=WOODD, width=5)
    elif name == 'fridge':
        d.rounded_rectangle([x - S(130), y - S(560), x + S(130), y], 14, fill=(235, 238, 242), outline=BLACK, width=7); d.line([(x - S(130), y - S(370)), (x + S(130), y - S(370))], fill=BLACK, width=5)
        d.rectangle([x + S(90), y - S(520), x + S(105), y - S(420)], fill=STEEL); d.rectangle([x + S(90), y - S(330), x + S(105), y - S(200)], fill=STEEL)
    elif name == 'snack':
        d.polygon([(x - S(60), y - S(160)), (x + S(60), y - S(160)), (x + S(70), y), (x - S(70), y)], fill=(255, 190, 40), outline=BLACK, width=5); d.text((x - S(40), y - S(110)), 'CHIPS', font=F(max(14, int(S(28)))), fill=(200, 40, 40))
    elif name == 'clock':
        d.ellipse([x - S(90), y - S(180), x + S(90), y], fill=WHITE, outline=BLACK, width=8); cx, cy = x, y - S(90)
        a = t * 4; d.line([(cx, cy), (cx + math.cos(a) * S(65), cy + math.sin(a) * S(65))], fill=BLACK, width=7); d.line([(cx, cy), (cx + math.cos(a / 12) * S(40), cy + math.sin(a / 12) * S(40))], fill=BLACK, width=9)
    elif name == 'envelope':
        d.rectangle([x - S(90), y - S(120), x + S(90), y], fill=WHITE, outline=BLACK, width=6); d.line([(x - S(90), y - S(120)), (x, y - S(50)), (x + S(90), y - S(120))], fill=BLACK, width=5); d.ellipse([x + S(55), y - S(150), x + S(105), y - S(100)], fill=(225, 45, 45))
    elif name == 'trash':
        d.polygon([(x - S(80), y - S(220)), (x + S(80), y - S(220)), (x + S(65), y), (x - S(65), y)], fill=STEEL, outline=BLACK, width=6); d.rectangle([x - S(95), y - S(240), x + S(95), y - S(220)], fill=(80, 85, 95))
    elif name == 'plant':
        d.polygon([(x - S(55), y - S(110)), (x + S(55), y - S(110)), (x + S(40), y), (x - S(40), y)], fill=(200, 100, 60), outline=BLACK, width=5)
        for a in (-.6, -.2, .2, .6): d.ellipse([x + math.sin(a) * S(80) - S(30), y - S(230) + abs(a) * S(60), x + math.sin(a) * S(80) + S(30), y - S(130) + abs(a) * S(60)], fill=(70, 170, 90), outline=BLACK, width=3)

def arrow(d, x, y, t):
    p = math.sin(t * 8) * 10
    d.polygon([(x - 45 + p, y - 32), (x + 25 + p, y), (x - 45 + p, y + 32)], fill=(225, 45, 45))

def chip(d, cx, cy, text, color, size=58, maxw=900):
    text = ''.join(ch for ch in text if ord(ch) < 0x2000 or ch in '→').strip()
    f = F(size); words = text.split(); lines = []; cur = ''
    for w_ in words:
        tt = (cur + ' ' + w_).strip()
        if d.textlength(tt, font=f) <= maxw - 60: cur = tt
        else: lines.append(cur); cur = w_
    lines.append(cur); lh = size + 14; bw = max(d.textlength(l, font=f) for l in lines) + 70; bh = lh * len(lines) + 40
    d.rounded_rectangle([cx - bw / 2, cy, cx + bw / 2, cy + bh], 22, fill=CHIP[color])
    fg = BLACK if color == 'yellow' else WHITE
    for i, l in enumerate(lines): d.text((cx, cy + 20 + i * lh + lh / 2 - 4), l, font=f, fill=fg, anchor='mm')
    return cy + bh

def outlined(d, xy, text, size, fill=WHITE, stroke=BLACK, sw=8):
    d.text(xy, text, font=F(size), fill=fill, anchor='mm', stroke_width=sw, stroke_fill=stroke)

SETS = {
    'kitchen': [('trash', 140, 1.0), ('kitchen', 760, 1.0)],
    'bedroom': [('window_night', 830, 1.0), ('bed', 700, .9)],
    'living': [('couch', 330, .9), ('tv', 850, 1.0)],
    'door': [('door', 870, 1.0), ('plant', 140, 1.0)],
    'desk': [('desk', 780, 1.0), ('plant', 130, .9)],
    'store': [('shelf', 780, 1.0)],
    'laundry': [('washer', 820, 1.0), ('basket', 140, 1.0)],
    'blank': [],
}

def frame(b, lt, gt, D):
    im = Image.new('RGB', (W, H), WHITE); d = ImageDraw.Draw(im)
    if b.get('card'):
        d.rectangle([0, 0, W, H], fill=(25, 25, 35)); prop(d, 'clock', W / 2, 860, 2.2, gt)
        txt = b['card'].split('|'); outlined(d, (W / 2, 1060), txt[0], 110, fill=(255, 214, 40), stroke=(25, 25, 35), sw=0)
        if len(txt) > 1: outlined(d, (W / 2, 1180), txt[1], 70, stroke=(25, 25, 35), sw=0)
        return im
    st = b.get('set', 'blank')
    for name, x, s in SETS.get(st, []): prop(d, name, x, FLOOR if name != 'window_night' else 900, s, gt)
    if st != 'blank': d.line([(0, FLOOR), (W, FLOOR)], fill=BLACK, width=6)
    pop = min(1, lt / .25)
    for i, p in enumerate(b.get('props', [])):
        name, x = p[0], p[1]; y = p[2] if len(p) > 2 else FLOOR; s = (p[3] if len(p) > 3 else 1.0) * (0.6 + .4 * pop)
        prop(d, name, x, y, s, gt)
    sx = b.get('x', 420)
    skip(d, sx, FLOOR, b, gt)
    if b.get('arrow'): arrow(d, b['arrow'][0], b['arrow'][1], gt)
    if b.get('label'): outlined(d, (W / 2, 250), b['label'], 92)
    if b.get('counter'): chip(d, W - 230, 330, b['counter'], 'yellow', 44, 420)
    d.rectangle([0, FLOOR + 3, W, 1760], fill=(236, 236, 238))
    y = 1330
    if b.get('cap'):
        sc = 0.85 + 0.15 * min(1, lt / .18)
        y = chip(d, W / 2, y, b['cap'], b.get('chip', 'red'), int(64 * sc))
    if b.get('cap2'): chip(d, W / 2, y + 26, b['cap2'], b.get('chip2', 'dark'), 46)
    return im

def build(ep, out):
    beats = ep['beats']
    segs, durs, sr = tts([b['say'] for b in beats], None)
    audio = np.concatenate(segs)
    # sfx at beat starts
    t0 = 0
    for b, dd in zip(beats, durs):
        if b.get('sfx'):
            s = sfx(b['sfx'], sr); i = int(t0 * sr); audio[i:i + len(s)] += s[:len(audio) - i]
        t0 += dd
    audio = audio / max(1e-6, np.abs(audio).max()) * .89
    sf.write('/tmp/skip_voice.wav', audio, sr)
    total = sum(durs); n = int(total * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', '/tmp/skip_voice.wav',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', out], stdin=subprocess.PIPE)
    starts = np.cumsum([0] + durs[:-1])
    bi = 0
    for fi in range(n):
        gt = fi / FPS
        while bi + 1 < len(beats) and gt >= starts[bi + 1]: bi += 1
        p.stdin.write(frame(beats[bi], gt - starts[bi], gt, durs[bi]).tobytes())
    p.stdin.close(); p.wait()
    print('TOTAL', round(total, 1))

if __name__ == '__main__':
    build(json.load(open(sys.argv[1])), sys.argv[2])
