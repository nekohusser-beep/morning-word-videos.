#!/usr/bin/env python3
"""Peppy competitor-style sleep thumbnail from a scene still.
Usage: make_thumb2.py OUT.jpg SCENE.jpg "TOP LINE" "BIG" "BADGE" "CHIP" ACC_R,G,B [rays_x]"""
import sys, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
out, scene, top, big, badge, chip, acc = sys.argv[1:8]
ACC = tuple(int(x) for x in acc.split(','))
W,H = 1280,720
img = Image.open(scene).convert('RGB').resize((W,H), Image.LANCZOS)
img = ImageEnhance.Color(img).enhance(1.55); img = ImageEnhance.Brightness(img).enhance(1.18); img = ImageEnhance.Contrast(img).enhance(1.12)
# light rays from the glow
rx = float(sys.argv[8]) if len(sys.argv)>8 else 0.62
cx, cy = int(W*rx), int(H*0.55)
ray = Image.new('L',(W,H),0); rd = ImageDraw.Draw(ray)
for k in range(24):
    a0 = k*math.pi*2/24; a1 = a0 + math.pi/48
    rd.polygon([(cx,cy),(cx+3000*math.cos(a0),cy+3000*math.sin(a0)),(cx+3000*math.cos(a1),cy+3000*math.sin(a1))], fill=70)
ray = ray.filter(ImageFilter.GaussianBlur(10))
img = Image.composite(Image.new('RGB',(W,H),(255,236,170)), img, ray)
# dark gradient on the left so the type pops
g = np.linspace(0.78,0.0,760)[None,:,None]*np.ones((H,1,1))
a = np.array(img).astype(np.float32); a[:,:760] *= (1-g*0.85); img = Image.fromarray(np.clip(a,0,255).astype(np.uint8))
d = ImageDraw.Draw(img)
fb = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def fit(t, path, maxw, start):
    s = start
    while ImageFont.truetype(path, s).getlength(t) > maxw: s -= 4
    return ImageFont.truetype(path, s)
def stroke(xy, t, f, fill, sw=9): d.text(xy, t, font=f, fill=fill, stroke_width=sw, stroke_fill=(10,6,20))
stroke((48,40), top, fit(top, fb, 760, 64), (255,255,255), 7)
stroke((40,112), big, fit(big, fb, 800, 250), ACC, 12)
for t,y,fill,tc in [(chip,430,(255,255,255),(20,10,40)), ("SOFT-SPOKEN  •  KJV  •  DARK SCREEN",508,(20,10,40),(255,255,255))]:
    f = fit(t, fb, 760, 46); w = int(f.getlength(t))+50
    d.rounded_rectangle((48,y,48+w,y+66), 16, fill=fill, outline=ACC, width=3); d.text((73,y+8), t, font=f, fill=tc)
f = fit(badge, fb, 800, 54); w = int(f.getlength(badge))+64
d.rounded_rectangle((48,606,48+w,690), 42, fill=(225,25,40), outline=(255,255,255), width=4); d.text((80,618), badge, font=f, fill=(255,255,255))
img.save(out, quality=93); print('saved', out)
