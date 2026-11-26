#!/usr/bin/env python3
"""Black Friday free stills -> render art. Removes the lunch-sauce stain the break-room reference carries on Dre's
forehead, and paints OUR text (sign, phone price, box label) so in-picture text is identical in every shot."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from scipy.ndimage import binary_dilation, label
FB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"; AW, AH = 1144, 2048
SIGN = (110, 330, 660, 436)
def prep(src, dst, box, phone=None, tvbox=False):
    im = Image.open(src).convert("RGB").resize((AW, AH), Image.LANCZOS); a = np.asarray(im).astype(int).copy()
    x0, y0, x1, y1 = box; r = a[y0:y1, x0:x1]
    m = (r[..., 0] > r[..., 1] + 25) & (r[..., 0] > r[..., 2] + 25)
    m = binary_dilation(m, iterations=4) & (r.sum(-1) > 120); r[m] = (253, 253, 253)
    lab, n = label(r.sum(-1) < 640); sizes = [(lab == i).sum() for i in range(1, n + 1)]; keep = 1 + int(np.argmax(sizes))
    edge = set(np.unique(np.concatenate([lab[-1, :], lab[:, -1], lab[0, :]])))
    for i in range(1, n + 1):
        if i != keep and i not in edge: r[lab == i] = (253, 253, 253)
    a[y0:y1, x0:x1] = r; im = Image.fromarray(a.astype("uint8")); d = ImageDraw.Draw(im)
    d.rounded_rectangle(SIGN, 18, fill=(214, 32, 38), outline=(20, 10, 14), width=7)
    f = ImageFont.truetype(FB, 50); t = "DOORS OPEN 6 AM"; w = d.textlength(t, font=f)
    d.text(((SIGN[0] + SIGN[2] - w) / 2, SIGN[1] + 16), t, font=f, fill=(255, 255, 255))
    if phone:
        px, py = phone; d.text((px, py), "$249", font=ImageFont.truetype(FB, 34), fill=(10, 40, 10))
        d.text((px + 2, py + 44), "ONLINE", font=ImageFont.truetype(FB, 17), fill=(10, 40, 10))
    if tvbox:
        d.rounded_rectangle([640, 1385, 800, 1470], 10, outline=(30, 30, 40), width=6); d.rectangle([652, 1397, 788, 1458], fill=(60, 120, 200))
        d.line([700, 1470, 740, 1470], fill=(30, 30, 40), width=8)
        fn = ImageFont.truetype(FB, 58); w = d.textlength("$299", font=fn); d.text((720 - w / 2, 1482), "$299", font=fn, fill=(214, 32, 38))
    im.save(dst, quality=95)
prep("art-free/a_two_11.webp", "art-free/a.jpg", (740, 900, 880, 1010))
prep("art-free/b_box_11.webp", "art-free/b.jpg", (740, 915, 885, 1030), phone=(606, 985), tvbox=True)
