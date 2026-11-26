#!/usr/bin/env python3
"""Black Friday free stills -> render art (v3, lit storefront). Free, repeatable.
- removes the lunch-sauce marks the break-room reference carries on Dre (forehead + cheek)
- blurs the garbled lettering the generator put in the shop windows
- paints OUR text (store sign, box label, phone price) so in-picture text is identical in every shot
- b3: the generator blanked Skip's face; his head is restored from c_box (same pose, same background)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from scipy.ndimage import binary_dilation, label
FB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"; AW, AH = 1144, 2048
def sauce(a, box, head=None):
    """Forehead (head=(cx, cy, r)): whiten everything in the box that lies inside the head circle and is not part of
    the scalp / outline / eye lines (dark shapes that run off the box edge). Cheek (head=None): whiten red-brown specks."""
    x0, y0, x1, y1 = box; r = a[y0:y1, x0:x1]; R, G, B = r[..., 0], r[..., 1], r[..., 2]
    if head is None:
        m0 = (R > G + 20) & (R > B + 20) & (G < 140) & (B < 130)
        r[binary_dilation(m0, iterations=5) & (r.sum(-1) > 150)] = (253, 253, 253)
    else:
        yy, xx = np.mgrid[y0:y1, x0:x1]; inside = (xx - head[0]) ** 2 + (yy - head[1]) ** 2 < head[2] ** 2
        lab, n = label(r.sum(-1) < 330)
        edge = set(np.unique(np.concatenate([lab[-1, :], lab[:, -1], lab[0, :], lab[:, 0]]))) - {0}
        prot = binary_dilation(np.isin(lab, list(edge)), iterations=2)
        r[inside & ~prot] = (253, 253, 253)
    a[y0:y1, x0:x1] = r
def prep(im, dst, forehead, cheek, head, box_dy=None, phone=False):
    im = im.convert("RGB").resize((AW, AH), Image.LANCZOS); a = np.asarray(im).astype(int).copy()
    sauce(a, forehead, head); sauce(a, cheek); im = Image.fromarray(a.astype("uint8"))
    for wx in ((55, 195), (985, 1130)):                       # garbled window lettering -> soft blur
        reg = (wx[0], 560, wx[1], 715); patch = im.crop(reg).filter(ImageFilter.GaussianBlur(22))
        mk = Image.new("L", patch.size, 0); ImageDraw.Draw(mk).rounded_rectangle([10, 10, patch.width - 10, patch.height - 10], 20, fill=255)
        im.paste(patch, reg[:2], mk.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(im)
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
c = Image.open("art-free/c_box_11.webp").convert("RGB"); b = Image.open("art-free/b3_11.webp").convert("RGB")
m = Image.new("L", b.size, 0); ImageDraw.Draw(m).ellipse([60, 395, 318, 705], fill=255)
b3 = Image.composite(c, b, m.filter(ImageFilter.GaussianBlur(6)))
prep(Image.open("art-free/a2_11.webp"), "art-free/a.jpg", (700, 915, 800, 1000), (826, 1092, 872, 1138), (832, 1012, 124))
prep(c, "art-free/c.jpg", (700, 925, 800, 1010), (822, 1106, 872, 1152), (830, 1022, 124), box_dy=0)
prep(b3, "art-free/b.jpg", (690, 930, 800, 1025), (815, 1105, 885, 1185), (837, 1037, 134), box_dy=15, phone=True)
