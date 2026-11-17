#!/usr/bin/env python3
"""Rebuild the approved John beach-dusk thumbnail for another book. Usage: make_thumb.py OUT.jpg "THE GOSPEL OF" "MATTHEW" "4.5 HOURS • FOR DEEP SLEEP" """
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
out, small, big, badge = sys.argv[1:5]
import os
HUE = int(os.environ.get('HUE','0'))  # 0-255 hue rotation so each book looks different
ACC = tuple(int(x) for x in os.environ.get('ACC','255,206,84').split(','))
src = Image.open('sleep/kit/thumb_john_v3.jpg').convert('RGB'); W,H = src.size
a = np.array(src).astype(np.float32)
cut = 880
strip = src.crop((1165, 0, 1280, H)).resize((cut, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
sa = np.array(strip).astype(np.float32) * np.linspace(0.6, 1.0, cut)[None,:,None]
bg = Image.fromarray(np.clip(sa,0,255).astype(np.uint8))
full = Image.new('RGB', (W,H)); full.paste(bg, (0,0)); full.paste(src.crop((cut,0,W,H)), (cut,0))
mask = np.zeros((H,W),np.float32); mask[:, 900:] = 1; mask[:, 850:900] = np.linspace(0,1,50)[None,:]
img = Image.composite(src, full, Image.fromarray((mask*255).astype(np.uint8)))
if HUE:
    h,sat,v = img.convert('HSV').split(); h = h.point(lambda x:(x+HUE)%256); img = Image.merge('HSV',(h,sat,v)).convert('RGB')
d = ImageDraw.Draw(img)
fb = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'; fs = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def fit(txt, path, maxw, start):
    s = start
    while ImageFont.truetype(path, s).getlength(txt) > maxw: s -= 4
    return ImageFont.truetype(path, s)
def stroke(xy, txt, f, fill):
    d.text(xy, txt, font=f, fill=fill, stroke_width=7, stroke_fill=(0,0,0))
stroke((48,64), small, fit(small, fb, 640, 78), (255,255,255))
stroke((40,150), big, fit(big, fb, 650, 220), ACC)
for txt, y in [("SOFT-SPOKEN KJV READING", 362), ("DARK SCREEN  +  CRASHING WAVES", 424)]:
    f = fit(txt, fs, 800, 44); w = int(f.getlength(txt))+44
    if y > 400: w = 908-48
    d.rounded_rectangle((48,y,48+w,y+54), 12, fill=(10,16,40), outline=ACC, width=2); d.text((70,y+4), txt, font=f, fill=(255,255,255))
f = fit(badge, fs, 780, 50); w = int(f.getlength(badge))+60
d.rounded_rectangle((48,576,48+w,646), 35, fill=(200,30,36)); d.text((78,584), badge, font=f, fill=(255,255,255))
img.save(out, quality=92); print('saved', out)
