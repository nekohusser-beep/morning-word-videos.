#!/usr/bin/env python3
"""Black Friday free stills -> render art (v4). Free, repeatable.
- Dre's head: ONE cleaned head (from a2) is used in all three stills, so goatee/hairline are identical everywhere.
  Cleaning = the lunch-sauce marks the break-room reference carries (forehead, cheek) and the little tick at the end
  of his mouth line (so a drawn open mouth fully covers the resting line). The mouth itself is left as drawn.
- garbled generator lettering in the shop is covered by our own SALE tags; sign / box label / phone price are ours too.
- b3: the generator blanked Skip's face; his head is restored from c_box (same pose, same background)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from scipy.ndimage import binary_dilation, label
FB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"; AW, AH = 1144, 2048
WHITE = (253, 253, 253)
def load(p): return (p if isinstance(p, Image.Image) else Image.open(p)).convert("RGB").resize((AW, AH), Image.LANCZOS)
def clean_head(im):
    a = np.asarray(im).astype(int).copy()
    # forehead sauce: hairline here is a flat line; rebuild it as black above / white below, only where the sauce was
    x0, y0, x1, y1 = 700, 905, 810, 1005; r = a[y0:y1, x0:x1]; R, G, B = r[..., 0], r[..., 1], r[..., 2]
    sauce = (R > G + 20) & (R > B + 20) & (G < 110) & (B < 110)
    cols = np.where(sauce.any(0))[0]; near = binary_dilation(sauce, iterations=9)
    clean_cols = [j for j in range(r.shape[1]) if j not in set(range(cols.min() - 10, cols.max() + 11))]
    hl = []
    for j in clean_cols:
        col = r[:, j].sum(-1); dark = np.where(col < 200)[0]; lite = np.where(col > 700)[0]
        if len(dark) and len(lite) and lite.min() > dark.min(): hl.append(lite[lite > dark.min()].min())
    hl = int(np.median(hl)) if hl else 0
    yy, xx = np.mgrid[y0:y1, x0:x1]; inside = (xx - 832) ** 2 + (yy - 1012) ** 2 < 122 ** 2
    r[near & inside & (yy - y0 >= hl) & (yy < 974)] = WHITE
    r[near & inside & (yy - y0 < hl)] = (14, 12, 18)
    lab, n = label(r.sum(-1) < 520)
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(ys) < 60 and ys.min() > 0 and xs.min() > 0 and ys.max() < r.shape[0] - 1 and xs.max() < r.shape[1] - 1 and (ys + y0).max() < 972:
            r[binary_dilation(lab == i, iterations=2)] = WHITE
    a[y0:y1, x0:x1] = r
    # cheek speck
    x0, y0, x1, y1 = 826, 1092, 872, 1138; r = a[y0:y1, x0:x1]; R, G, B = r[..., 0], r[..., 1], r[..., 2]
    m = (R > G + 20) & (R > B + 20) & (G < 140) & (B < 130); r[binary_dilation(m, iterations=5) & (r.sum(-1) > 150)] = WHITE; a[y0:y1, x0:x1] = r
    # mouth: keep the drawn line, drop the tick at its end (the mouth is the dark shape that does not touch the goatee)
    x0, y0, x1, y1 = 765, 1070, 850, 1135; r = a[y0:y1, x0:x1]; lab, n = label(r.sum(-1) < 420)
    edge = set(np.unique(np.concatenate([lab[-1, :], lab[:, -1], lab[0, :], lab[:, 0]]))) - {0}
    global MOUTH_XY
    goatee = binary_dilation(np.isin(lab, list(edge)), iterations=3)
    for i in range(1, n + 1):
        if i in edge: continue
        ys, xs = np.where(lab == i)
        if len(ys) >= 25: MOUTH_XY = (x0 + int(xs.min()), x0 + int(xs.max()) - 7, y0 + int(np.median(ys)))
    r[(r.sum(-1) < 735) & ~goatee] = WHITE                      # line, nub and stray grey specks inside the goatee
    a[y0:y1, x0:x1] = r
    # any sauce-red left inside the head near the forehead
    x0, y0, x1, y1 = 690, 895, 815, 1010; r = a[y0:y1, x0:x1]; R, G, B = r[..., 0], r[..., 1], r[..., 2]
    yy, xx = np.mgrid[y0:y1, x0:x1]; ins = (xx - 832) ** 2 + (yy - 1012) ** 2 < 133 ** 2
    r[binary_dilation((R > G + 22) & (R > B + 22) & ins, iterations=2) & ins & (r.sum(-1) > 200)] = WHITE; a[y0:y1, x0:x1] = r
    im = Image.fromarray(a.astype("uint8")); xa, xb, ym = MOUTH_XY
    ImageDraw.Draw(im).line([xa, ym, xb, ym], fill=(14, 12, 18), width=6)
    return im
def tag(d, box, txt, size):
    d.rounded_rectangle(box, 10, fill=(214, 32, 38), outline=(20, 10, 14), width=4)
    f = ImageFont.truetype(FB, size); w = d.textlength(txt, font=f); bb = d.textbbox((0, 0), txt, font=f)
    d.text(((box[0] + box[2] - w) / 2, (box[1] + box[3]) / 2 - (bb[1] + bb[3]) / 2), txt, font=f, fill=(255, 255, 255))
def finish(im, dst, box_dy=None, phone=False, sign=(778, 864)):
    import cv2
    arr = np.asarray(im).copy(); mk = np.zeros(arr.shape[:2], "uint8"); mk[sign[0]:sign[1], 982:1094] = 255
    im = Image.fromarray(cv2.inpaint(arr, mk, 5, cv2.INPAINT_NS))      # garbled shelf sign -> filled from its surroundings
    d = ImageDraw.Draw(im)
    tag(d, (66, 588, 186, 672), "SALE", 38); tag(d, (988, 596, 1112, 690), "SALE", 40)
    d.rounded_rectangle([250, 296, 894, 412], 18, fill=(214, 32, 38), outline=(20, 10, 14), width=7)
    f = ImageFont.truetype(FB, 78); t = "BLACK FRIDAY"; w = d.textlength(t, font=f); d.text(((AW - w) / 2, 303), t, font=f, fill=(255, 255, 255))
    if box_dy is not None:
        y = 1322 + box_dy
        d.rounded_rectangle([640, y, 786, y + 82], 10, outline=(30, 30, 40), width=6); d.rectangle([652, y + 12, 774, y + 70], fill=(60, 120, 200))
        d.line([694, y + 84, 732, y + 84], fill=(30, 30, 40), width=8)
        fn = ImageFont.truetype(FB, 60); w = d.textlength("$299", font=fn); d.text((713 - w / 2, y + 94), "$299", font=fn, fill=(214, 32, 38))
    if phone:
        fn = ImageFont.truetype(FB, 40); w = d.textlength("$249", font=fn); d.text((617 - w / 2, 815), "$249", font=fn, fill=(10, 40, 10))
        fn = ImageFont.truetype(FB, 20); w = d.textlength("ONLINE", font=fn); d.text((617 - w / 2, 868), "ONLINE", font=fn, fill=(10, 40, 10))
    im.save(dst, quality=95)
def with_head(im, head, dx, dy):
    m = Image.new("L", (AW, AH), 0); ImageDraw.Draw(m).ellipse([832 - 143 + dx, 1012 - 143 + dy, 832 + 143 + dx, 1012 + 143 + dy], fill=255)
    sh = Image.new("RGB", (AW, AH)); sh.paste(head, (dx, dy)); return Image.composite(sh, im, m.filter(ImageFilter.GaussianBlur(2)))
cw = Image.open("art-free/c_box_11.webp").convert("RGB"); bw = Image.open("art-free/b3_11.webp").convert("RGB")
m = Image.new("L", bw.size, 0); ImageDraw.Draw(m).ellipse([60, 395, 318, 705], fill=255)
b3 = Image.composite(cw, bw, m.filter(ImageFilter.GaussianBlur(6)))
a = clean_head(load("art-free/a2_11.webp"))
import sys
DC = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (-2, 10)
DB = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (5, 25)
c = with_head(load(cw), a, *DC); b = with_head(load(b3), a, *DB)
print("mouth", MOUTH_XY); finish(a.copy(), "art-free/a.jpg"); finish(c, "art-free/c.jpg", box_dy=0, sign=(796, 874)); finish(b, "art-free/b.jpg", box_dy=15, phone=True, sign=(786, 888))
