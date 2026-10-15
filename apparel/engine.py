import math, os
from PIL import Image, ImageDraw, ImageFont

F = os.path.join(os.path.dirname(__file__), 'fonts')
W, H = 4200, 4800

def font(name, size, var=None):
    f = ImageFont.truetype(os.path.join(F, name), size)
    if var:
        try: f.set_variation_by_name(var)
        except Exception: pass
    return f

FONTS = {
    'bebas': ('BebasNeue-Regular.ttf', None), 'anton': ('Anton-Regular.ttf', None),
    'archivo': ('ArchivoBlack-Regular.ttf', None), 'abril': ('AbrilFatface-Regular.ttf', None),
    'playfair': ('PlayfairDisplay.ttf', 'Bold'), 'playfairb': ('PlayfairDisplay.ttf', 'Black'),
    'cinzel': ('Cinzel.ttf', 'Bold'), 'cinzelr': ('Cinzel.ttf', 'Regular'),
    'cormorant': ('CormorantGaramond.ttf', 'SemiBold'), 'cormorantb': ('CormorantGaramond.ttf', 'Bold'),
    'oswald': ('Oswald.ttf', 'SemiBold'), 'oswaldb': ('Oswald.ttf', 'Bold'),
    'mont': ('Montserrat.ttf', 'SemiBold'), 'montb': ('Montserrat.ttf', 'ExtraBold'),
    'vibes': ('GreatVibes-Regular.ttf', None), 'allura': ('Allura-Regular.ttf', None),
    'sacramento': ('Sacramento-Regular.ttf', None),
}

def F_(key, size):
    n, v = FONTS[key]; return font(n, size, v)

def text_w(d, s, f, track=0):
    if not track: return d.textlength(s, font=f)
    return sum(d.textlength(c, font=f) for c in s) + track * (len(s) - 1)

def draw_text(d, cx, y, s, f, fill, track=0):
    """centered at cx, top y; returns bottom y"""
    w = text_w(d, s, f, track)
    x = cx - w / 2
    bb = d.textbbox((0, 0), s, font=f)
    top = y - bb[1]
    if not track:
        d.text((x, top), s, font=f, fill=fill)
    else:
        for c in s:
            d.text((x, top), c, font=f, fill=fill)
            x += d.textlength(c, font=f) + track
    return y + (bb[3] - bb[1])

def fit_size(d, s, key, maxw, start, track_ratio=0):
    size = start
    while size > 40:
        f = F_(key, size)
        if text_w(d, s, f, size * track_ratio) <= maxw: return f, size
        size -= 10
    return F_(key, size), size

def cross(d, cx, cy, h, fill, thick=None):
    t = thick or h * 0.16
    d.rectangle([cx - t / 2, cy - h / 2, cx + t / 2, cy + h / 2], fill=fill)
    arm_y = cy - h / 2 + h * 0.3
    d.rectangle([cx - h * 0.33, arm_y - t / 2, cx + h * 0.33, arm_y + t / 2], fill=fill)

def star(d, cx, cy, r, fill, points=8, inner=0.38):
    pts = []
    for i in range(points * 2):
        a = math.pi / points * i - math.pi / 2
        rr = r if i % 2 == 0 else r * inner
        if i % 4 == 0 and points == 8: rr = r * (1.0 if i == 0 or i == 8 else 0.75)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)

def rule(d, cx, y, w, fill, t=14, gap=0, dot=False):
    if dot:
        d.rectangle([cx - w / 2, y - t / 2, cx - gap, y + t / 2], fill=fill)
        d.rectangle([cx + gap, y - t / 2, cx + w / 2, y + t / 2], fill=fill)
    else:
        d.rectangle([cx - w / 2, y - t / 2, cx + w / 2, y + t / 2], fill=fill)

def leaf(d, cx, cy, l, ang, fill):
    # simple pointed leaf as polygon
    pts = []
    for i in range(41):
        t = i / 40
        x = t * l; y = math.sin(math.pi * t) * l * 0.22
        pts.append((x, y))
    for i in range(40, -1, -1):
        t = i / 40
        pts.append((t * l, -math.sin(math.pi * t) * l * 0.22))
    ca, sa = math.cos(ang), math.sin(ang)
    d.polygon([(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts], fill=fill)

def wheat(d, cx, cy, h, fill, lean=0.0):
    # stalk + grains
    top = (cx + lean * h, cy - h)
    d.line([(cx, cy), top], fill=fill, width=int(h * 0.025))
    for i in range(7):
        t = 0.35 + i * 0.09
        px = cx + lean * h * t; py = cy - h * t
        a = math.atan2(-h, lean * h)
        leaf(d, px, py, h * 0.16, a + 0.6, fill)
        leaf(d, px, py, h * 0.16, a - 0.6, fill)
    leaf(d, top[0], top[1], h * 0.14, math.atan2(-h, lean * h), fill)

def branch(d, cx, cy, length, ang, fill, n=6):
    ex, ey = cx + length * math.cos(ang), cy + length * math.sin(ang)
    d.line([(cx, cy), (ex, ey)], fill=fill, width=int(length * 0.025))
    for i in range(n):
        t = (i + 1) / (n + 1)
        px, py = cx + (ex - cx) * t, cy + (ey - cy) * t
        leaf(d, px, py, length * 0.22, ang - 0.7, fill)
        leaf(d, px, py, length * 0.22, ang + 0.7, fill)
    leaf(d, ex, ey, length * 0.22, ang, fill)

def snowflake(d, cx, cy, r, fill):
    w = int(r * 0.09)
    for k in range(6):
        a = math.pi / 3 * k
        ex, ey = cx + r * math.cos(a), cy + r * math.sin(a)
        d.line([(cx, cy), (ex, ey)], fill=fill, width=w)
        for t in (0.55, 0.8):
            bx, by = cx + r * t * math.cos(a), cy + r * t * math.sin(a)
            for s in (-1, 1):
                aa = a + s * 0.7
                d.line([(bx, by), (bx + r * 0.22 * math.cos(aa), by + r * 0.22 * math.sin(aa))], fill=fill, width=w)

def new():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)

def finish(im, path):
    bb = im.getbbox()
    if bb:
        # crop to content with padding, then place top-centered on canvas (prints sit high on chest)
        pad = 60
        c = im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(W, bb[2] + pad), min(H, bb[3] + pad)))
        out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        scale = min((W - 200) / c.width, (H * 0.92) / c.height, 1.0)
        if scale < 1: c = c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)
        out.paste(c, ((W - c.width) // 2, 40), c)
        im = out
    im.save(path, optimize=True)
    return path
