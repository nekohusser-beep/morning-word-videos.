#!/usr/bin/env python3
"""Sleep long-form thumbnail v4 (Nov 6 2026): approved 'our lady' beach-dusk base, clearer words.
mkthumb2.py OUT.jpg TOP BIG RANGE SOUND BADGE  (ACC env = r,g,b accent)"""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
out, top, big, rng, snd, badge = sys.argv[1:7]
ACC = tuple(int(x) for x in os.environ.get('ACC','255,206,84').split(','))
src = Image.open('/home/claude/morning-word-videos./sleep/kit/thumb_john_v3.jpg').convert('RGB'); W,H = src.size
cut = 880
strip = src.crop((1165, 0, 1280, H)).resize((cut, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
sa = np.array(strip).astype(np.float32) * np.linspace(0.55, 1.0, cut)[None,:,None]
full = Image.new('RGB', (W,H)); full.paste(Image.fromarray(np.clip(sa,0,255).astype(np.uint8)), (0,0)); full.paste(src.crop((cut,0,W,H)), (cut,0))
mask = np.zeros((H,W),np.float32); mask[:, 900:] = 1; mask[:, 850:900] = np.linspace(0,1,50)[None,:]
img = Image.composite(src, full, Image.fromarray((mask*255).astype(np.uint8)))
d = ImageDraw.Draw(img)
fb='/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'; fs='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def fit(t,p,maxw,start,minsz=20):
    s=start
    while s>minsz and ImageFont.truetype(p,s).getlength(t)>maxw: s-=4
    return ImageFont.truetype(p,s)
def stroke(xy,t,f,fill,sw=7): d.text(xy,t,font=f,fill=fill,stroke_width=sw,stroke_fill=(0,0,0))
stroke((50,48), top, fit(top,fb,700,74), (255,255,255))
fbig = fit(big,fb,800,230)
while d.textbbox((40,128), big, font=fbig)[3] > 296: fbig = ImageFont.truetype(fb, fbig.size-6)
stroke((40,128), big, fbig, ACC, 8)
bb = d.textbbox((40,128), big, font=fbig); y = bb[3] + 28
y = min(y, 330); f = fit(rng, fs, 800, 60); w = int(f.getlength(rng)) + 48
d.rounded_rectangle((48,y,48+w,y+76), 14, fill=(10,16,40), outline=ACC, width=3); d.text((72,y+6), rng, font=f, fill=(255,255,255))
y = 424  # covers the old chip edge baked into the base (ends x=905)
f2 = fit(snd, fs, 820, 42)
d.rounded_rectangle((48,y,912,y+60), 12, fill=(10,16,40), outline=(255,255,255), width=2); d.text((72,y+6), snd, font=f2, fill=(230,235,255))
f3 = fit(badge, fs, 800, 50); w3 = int(f3.getlength(badge)) + 60
d.rounded_rectangle((48,592,48+w3,662), 35, fill=(200,30,36)); d.text((78,600), badge, font=f3, fill=(255,255,255))
img.save(out, quality=92); print('saved', out)
