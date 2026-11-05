#!/usr/bin/env python3
"""Blessed Prayers KJV verse card, 1080x1080, drawn locally (free replacement for the Orshot template).

  python3 tools/cards/verse_card.py --verse "..." --ref "Matthew 11:28" \
      --eyebrow "SATURDAY" --reflection "He meant it." --out card.jpg
Batch: --batch cards.json  (list of objects with verse, ref, eyebrow, reflection, out)
"""
import argparse, json, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(HERE, "fonts", n)
W = H = 1080
BG = (12, 11, 10)
GOLD = (212, 175, 55)
CREAM = (242, 234, 218)
MUTED = (176, 166, 148)


def font(name, size, weight):
    f = ImageFont.truetype(F(name), size)
    f.set_variation_by_name(weight)
    return f


def wrap(draw, text, fnt, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def spaced(draw, xy, text, fnt, fill, track):
    x, y = xy
    total = sum(draw.textlength(c, font=fnt) for c in text) + track * (len(text) - 1)
    x = x - total / 2
    for c in text:
        draw.text((x, y), c, font=fnt, fill=fill)
        x += draw.textlength(c, font=fnt) + track


def card(verse, ref, eyebrow, reflection, out, brand="BLESSED PRAYERS"):
    img = Image.new("RGB", (W, H), BG)
    glow = Image.new("RGB", (W, H), BG)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((140, 120, 940, 920), fill=(58, 44, 18))
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(190)), 0.9)
    d = ImageDraw.Draw(img)

    eb = font("Montserrat.ttf", 26, "SemiBold")
    spaced(d, (W / 2, 150), eyebrow.upper(), eb, GOLD, 7)
    d.line((W / 2 - 40, 205, W / 2 + 40, 205), fill=GOLD, width=2)

    # fit the verse: shrink until it fits the box
    box_w, box_h = 840, 520
    for size in range(68, 30, -2):
        vf = font("CormorantGaramond.ttf", size, "Medium")
        lines = wrap(d, "“" + verse.strip().strip('"') + "”", vf, box_w)
        lh = int(size * 1.22)
        if lh * len(lines) <= box_h:
            break
    group = lh * len(lines) + 28 + 70 + (30 + 46 * min(2, len(wrap(d, reflection, font("CormorantGaramond-Italic.ttf", 36, "Medium Italic"), 760))) if reflection else 0)
    top = 240 + (720 - group) / 2
    for i, ln in enumerate(lines):
        d.text((W / 2, top + i * lh), ln, font=vf, fill=CREAM, anchor="ma")
    y = top + lh * len(lines) + 28

    rf = font("Montserrat.ttf", 28, "Medium")
    spaced(d, (W / 2, y), f"{ref.upper()}  ·  KJV", rf, GOLD, 4)
    y += 70
    d.line((W / 2 - 40, y, W / 2 + 40, y), fill=GOLD, width=2)

    if reflection:
        ff = font("CormorantGaramond-Italic.ttf", 36, "Medium Italic")
        for i, ln in enumerate(wrap(d, reflection, ff, 760)[:2]):
            d.text((W / 2, y + 30 + i * 46), ln, font=ff, fill=MUTED, anchor="ma")

    bf = font("Montserrat.ttf", 22, "SemiBold")
    spaced(d, (W / 2, H - 80), brand, bf, GOLD, 8)
    img.save(out, quality=93)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verse"); p.add_argument("--ref"); p.add_argument("--eyebrow", default="")
    p.add_argument("--reflection", default=""); p.add_argument("--out", default="card.jpg")
    p.add_argument("--batch")
    a = p.parse_args()
    jobs = json.load(open(a.batch)) if a.batch else [vars(a)]
    for j in jobs:
        print(card(j["verse"], j["ref"], j.get("eyebrow", ""), j.get("reflection", ""), j["out"]))
