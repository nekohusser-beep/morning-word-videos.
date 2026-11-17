#!/usr/bin/env python3
"""1280x720 thumbnail from the animated scene: zoomed burning bush, big chunky title, gold accent. Free (PIL only)."""
import sys, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

SP = sys.argv[1]
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_scene as rsn

fr = rsn.frame(9.0).convert("RGB")          # 1920x1080
Z = 1.38
cw, ch = int(1920 / Z), int(1080 / Z)
bx, by = 0.64 * 1920, 0.70 * 1080
x0 = int(min(max(bx - 0.70 * cw, 0), 1920 - cw))
y0 = int(min(max(by - 0.60 * ch, 0), 1080 - ch))
im = fr.crop((x0, y0, x0 + cw, y0 + ch)).resize((1280, 720), Image.LANCZOS)
im = ImageEnhance.Contrast(im).enhance(1.12)
im = ImageEnhance.Color(im).enhance(1.18)
im = ImageEnhance.Brightness(im).enhance(1.10)

# darken the left side so the text reads, keep the bush bright
a = np.asarray(im, dtype=np.float32) / 255.0
xs = np.linspace(0, 1, 1280)[None, :, None]
shade = 0.40 + 0.60 * np.clip((xs - 0.05) / 0.50, 0, 1) ** 1.2
a = a * shade
# soft vignette
yy, xx = np.mgrid[0:720, 0:1280]
v = 1 - 0.35 * (((xx - 640) / 760) ** 2 + ((yy - 360) / 460) ** 2)
a = a * np.clip(v, 0.5, 1)[:, :, None]
im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def font(sz):
    for p in glob.glob("/usr/share/fonts/**/Poppins-Bold.ttf", recursive=True):
        return ImageFont.truetype(p, sz)
    raise SystemExit("Poppins-Bold not found")


d = ImageDraw.Draw(im)
lines = [("WHO REALLY", (255, 255, 255)), ("SPOKE TO", (255, 255, 255)), ("PHARAOH?", (255, 206, 92))]
sz = 128
y = 150
for t, col in lines:
    f = font(sz)
    d.text((58, y), t, font=f, fill=col, stroke_width=7, stroke_fill=(10, 6, 4))
    y += int(sz * 1.08)
# tag pill
tf = font(34)
tag = "BIBLE STORY FOR SLEEP"
w = d.textlength(tag, font=tf)
d.rounded_rectangle((58, 62, 58 + w + 44, 62 + 62), radius=31, fill=(255, 206, 92))
d.text((80, 66), tag, font=tf, fill=(18, 10, 6))
out = f"{SP}/thumbnail.jpg"
im.save(out, quality=92)
print("saved", out)
