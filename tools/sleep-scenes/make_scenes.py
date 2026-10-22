#!/usr/bin/env python3
"""Free, text-free calm scene stills (procedural, no credits). Usage: make_scenes.py OUT_DIR [W=3840] [H=2160]"""
import sys, numpy as np
from PIL import Image, ImageFilter
out = sys.argv[1]; W = int(sys.argv[2]) if len(sys.argv)>2 else 3840; H = int(sys.argv[3]) if len(sys.argv)>3 else 2160
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); yn = yy/H; xn = xx/W
def grad(stops):
    ys = [s[0] for s in stops]; img = np.zeros((H,W,3),np.float32)
    for c in range(3): img[...,c] = np.interp(yn, ys, [s[1][c] for s in stops])
    return img
def glow(img, cx, cy, r, col, k=1.0):
    d = np.sqrt((xn-cx)**2*(W/H)**2 + (yn-cy)**2); g = np.exp(-(d/r)**2)[...,None]
    return img + g*np.array(col,np.float32)*k
def stars(img, n=900, top=0.55):
    for _ in range(n):
        x=int(rng.random()*W); y=int(rng.random()*H*top); b=rng.random()**3*200+40; s=rng.integers(1,4)
        img[max(0,y-s//2):y+s, max(0,x-s//2):x+s] += b
    return img
def ridge(base, amp, freq, seed, rough=3):
    r = np.random.default_rng(seed); x = np.linspace(0,1,W); h = np.zeros(W)
    for o in range(rough): h += r.random()*np.sin(x*freq*(2**o)*np.pi*2 + r.random()*6)*amp/(2**o)
    return base + h
def hills(img, layers):
    for base, amp, freq, seed, col in layers:
        top = ridge(base, amp, freq, seed)*H; mask = (yy > top[None,:])[...,None]
        img = np.where(mask, np.array(col,np.float32), img)
    return img
def water(img, hz, top_col, bot_col, cx, cy_light, col):
    m = (yy > hz*H); t = np.clip((yn-hz)/(1-hz),0,1)[...,None]
    w = np.array(top_col,np.float32)*(1-t) + np.array(bot_col,np.float32)*t
    ripple = (np.sin(yy*0.09 + np.sin(xx*0.004)*6)*0.5+0.5)[...,None]
    w = w*(0.88+0.24*ripple)
    d = np.abs(xn-cx)*(W/H); streak = np.exp(-(d/(0.03+0.25*(yn-hz)))**2)*t[...,0]*(0.4+0.6*ripple[...,0])
    w = w + streak[...,None]*np.array(col,np.float32)
    return np.where(m[...,None], w, img)
def save(img, name):
    img = np.clip(img,0,255).astype(np.uint8); im = Image.fromarray(img).filter(ImageFilter.GaussianBlur(1.2))
    n = rng.normal(0,2.2,(H,W,1)); arr = np.clip(np.array(im,np.float32)+n,0,255).astype(np.uint8)
    Image.fromarray(arr).save(f"{out}/{name}.jpg", quality=90); print("saved", name)
import os; os.makedirs(out, exist_ok=True)
# 1 dusk beach, low sun, waves
i = grad([(0,(18,22,52)),(0.35,(70,52,96)),(0.5,(220,130,90)),(0.52,(250,190,120))]); i = glow(i,0.5,0.5,0.22,(255,170,90),0.9)
i = water(i,0.52,(120,90,100),(18,26,48),0.5,0.5,(255,170,100)); save(i,"01-dusk-sea")
# 2 starry night, still lake, moon
i = grad([(0,(4,8,24)),(0.5,(18,30,64)),(0.58,(40,52,88))]); i = stars(i); i = glow(i,0.72,0.2,0.12,(200,215,255),0.7)
i[int(H*0.19):int(H*0.21), int(W*0.715):int(W*0.725)] += 255
i = hills(i,[(0.55,0.03,1.3,3,(8,12,26))]); i = water(i,0.6,(34,46,80),(6,10,24),0.72,0.2,(190,205,255)); save(i,"02-moon-lake")
# 3 sunrise over hills
i = grad([(0,(40,60,120)),(0.35,(190,120,140)),(0.55,(255,200,130))]); i = glow(i,0.35,0.55,0.25,(255,210,140),1.0)
i = hills(i,[(0.62,0.04,1.1,5,(110,80,110)),(0.70,0.05,1.7,8,(70,56,90)),(0.82,0.05,2.1,11,(36,34,56))]); save(i,"03-sunrise-hills")
# 4 candle glow in dark room
i = grad([(0,(8,6,8)),(1,(22,14,12))]); i = glow(i,0.5,0.55,0.35,(120,60,20),0.9); i = glow(i,0.5,0.52,0.07,(255,190,90),1.2)
i[int(H*0.50):int(H*0.58), int(W*0.4985):int(W*0.5015)] = [255,230,170]; save(i,"04-candle")
# 5 dusk shepherd field
i = grad([(0,(30,36,84)),(0.4,(120,84,120)),(0.6,(240,170,110))]); i = glow(i,0.62,0.6,0.2,(255,190,120),0.9)
i = hills(i,[(0.62,0.03,1.4,21,(76,66,86)),(0.72,0.04,1.2,22,(42,44,58)),(0.86,0.03,1.0,23,(20,24,30))]); save(i,"05-dusk-field")
# 6 aurora-ish night sky over hills
i = grad([(0,(4,10,26)),(0.6,(10,34,52))]); i = stars(i,700)
band = np.exp(-((yn-0.28-0.08*np.sin(xn*7))/0.07)**2)[...,None]*np.array([30,150,110],np.float32)
i = i+band*(0.5+0.5*np.sin(xn*13)[...,None]**2); i = hills(i,[(0.8,0.05,1.5,31,(4,10,16))]); save(i,"06-night-glow")
# 7 pale dawn sea mist
i = grad([(0,(150,170,200)),(0.5,(230,210,210)),(0.55,(240,225,215))]); i = glow(i,0.5,0.55,0.3,(255,235,210),0.6)
i = water(i,0.56,(200,190,200),(70,86,120),0.5,0.56,(255,235,210)); save(i,"07-dawn-mist")
# 8 deep blue twilight hills
i = grad([(0,(10,16,44)),(0.5,(40,56,110)),(0.62,(120,110,150))]); i = stars(i,300,0.4)
i = hills(i,[(0.66,0.04,1.2,41,(60,66,110)),(0.76,0.05,1.8,42,(30,34,66)),(0.88,0.04,1.3,43,(12,14,28))]); save(i,"08-twilight-hills")
