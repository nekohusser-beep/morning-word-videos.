#!/usr/bin/env python3
"""Photo-background KJV verse card, 1080x1920, with our lady in a circle at the bottom.

  python3 tools/cards/mist_card.py --verse "..." --ref "Romans 8:28" --bg photo.jpg --out card.jpg
  (no --bg: draws a soft misty-mountain background so the card still renders)
--bg must be a photo we own or have licence for (Gemini-made, Pexels/Unsplash). Never a screenshot from another app.
Lady circle: tools/cards/lady_circle.png (cropped from the approved sleep-channel thumbnail).
"""
import argparse, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
CREAM = (246, 244, 238)


def font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(HERE, "fonts", name), size)
    if weight:
        f.set_variation_by_name(weight)
    return f


def wrap(d, text, fnt, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def mist_bg(seed=8):
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, H)[:, None]
    top, mid, bot = np.array([112, 148, 156.]), np.array([84, 120, 130.]), np.array([30, 56, 66.])
    base = np.where(y < .6, top + (mid - top) * (y / .6)[..., None] if False else 0, 0)
    g = np.zeros((H, W, 3))
    for c in range(3):
        col = np.interp(y[:, 0], [0, .55, 1], [top[c], mid[c], bot[c]])
        g[:, :, c] = col[:, None]
    noise = np.zeros((H, W))
    for s, a in ((8, .5), (16, .3), (40, .2)):
        n = rng.random((H // s + 2, W // s + 2))
        noise += a * np.array(Image.fromarray((n * 255).astype("uint8")).resize((W, H), Image.BICUBIC)) / 255.
    g += (noise[..., None] - .5) * 46
    img = Image.fromarray(np.clip(g, 0, 255).astype("uint8"))
    d = ImageDraw.Draw(img, "RGBA")
    d.polygon([(380, 1020), (560, 640), (700, 560), (860, 720), (1080, 880), (1080, 1100), (380, 1100)], fill=(170, 195, 202, 150))
    img = img.filter(ImageFilter.GaussianBlur(14))
    d = ImageDraw.Draw(img, "RGBA")
    r = random.Random(seed)
    for row, (yb, hgt, alpha) in enumerate(((1330, 260, 110), (1450, 330, 170), (1560, 420, 235))):
        x = -40
        while x < W + 40:
            h = hgt * r.uniform(.6, 1.0); w = h * .34
            d.polygon([(x, yb), (x + w / 2, yb - h), (x + w, yb)], fill=(24, 48, 56, alpha))
            x += w * r.uniform(.5, .8)
        d.rectangle((0, yb, W, H), fill=(24, 48, 56, alpha))
        img = img.filter(ImageFilter.GaussianBlur(2.2 - row * .6)); d = ImageDraw.Draw(img, "RGBA")
    return img


def cover(img):
    s = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    x, y = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((x, y, x + W, y + H))


def card(verse, ref, out, bg=None, label="Verse of the Day", tag="Soft-spoken KJV Bible readings for sleep"):
    img = cover(Image.open(bg).convert("RGB")) if bg else mist_bg()
    img = ImageEnhance.Brightness(img).enhance(.82)
    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for i in range(H):
        sd.line((0, i, W, i), fill=int(110 * (i / H) ** 1.6 + 30))
    img = Image.composite(Image.new("RGB", (W, H), (8, 20, 26)), img, shade)
    d = ImageDraw.Draw(img)
    lf = font("Montserrat.ttf", 38, "Medium")
    d.text((84, 560), label, font=lf, fill=CREAM)
    d.text((84, 622), f"{ref} KJV", font=lf, fill=CREAM)
    for size in range(104, 50, -2):
        vf = font("CormorantGaramond.ttf", size, "Medium")
        lines = wrap(d, verse.strip(), vf, W - 168)
        lh = int(size * 1.2)
        if 720 + lh * len(lines) <= 1440:
            break
    for i, ln in enumerate(lines):
        d.text((84, 720 + i * lh), ln, font=vf, fill=CREAM)
    av = Image.open(os.path.join(HERE, "lady_circle.png")).resize((230, 230), Image.LANCZOS)
    ring = Image.new("RGBA", (246, 246), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((0, 0, 245, 245), fill=(*CREAM, 235))
    ring.paste(av, (8, 8), av)
    cy = 1560
    img.paste(ring, ((W - 246) // 2, cy), ring)
    tf = font("Montserrat.ttf", 27, "Medium")
    d = ImageDraw.Draw(img)
    d.text((W / 2, cy + 246 + 22), tag, font=tf, fill=CREAM, anchor="ma")
    img.save(out, quality=93)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verse", required=True); p.add_argument("--ref", required=True)
    p.add_argument("--bg"); p.add_argument("--out", default="card.jpg")
    a = p.parse_args()
    print(card(a.verse, a.ref, a.out, a.bg))
