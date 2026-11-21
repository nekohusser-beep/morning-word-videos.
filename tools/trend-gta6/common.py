import numpy as np, cv2, json, math, subprocess, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
GF = '/usr/share/fonts/truetype/google-fonts/'
ANTON = GF + 'ofl/anton/Anton-Regular.ttf'
LORA = GF + 'Lora-Variable.ttf'
LORAI = GF + 'Lora-Italic-Variable.ttf'
MONT = GF + 'ofl/montserrat/Montserrat[wght].ttf'
POP = GF + 'Poppins-Bold.ttf'
WHITE = (255, 255, 255); RED = (255, 48, 48); GOLD = (255, 206, 92); YEL = (255, 214, 10); GREY = (196, 202, 214)

AL = json.load(open('align.json'))
GAP = {'hook': 0.18, 'ritual': 0.30, 'egg': 0.45, 'money': 0.55, 'psalm': 0.30, 'eph': 0.35, 'house': 0.35, 'prayer': 0.30, 'ask': 1.10}
ORDER = ['hook', 'ritual', 'egg', 'money', 'psalm', 'eph', 'house', 'prayer', 'ask']
START = {}; _t = 0.10
for _k in ORDER:
    START[_k] = round(_t, 3); _t += AL[_k]['dur'] + GAP[_k]
TOTAL = round(_t, 2)
LEAD = 0.05


def wt(line, i):
    """absolute time word i of a line is spoken"""
    return START[line] + AL[line]['heard'][i][1] - LEAD


def lend(line):
    return START[line] + AL[line]['dur']


def font(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f


def tw(text, f, track=0):
    if track: return sum(f.getlength(c) for c in text) + track * (len(text) - 1)
    return f.getlength(text)


def _draw(d, xy, text, f, fill, stroke=0, track=0, stroke_fill=(0, 0, 0)):
    if not track:
        d.text(xy, text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill); return
    x, y = xy
    for c in text:
        d.text((x, y), c, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill); x += f.getlength(c) + track


_wc = {}


def word_img(text, f, fill, stroke=0, shadow=14, sh_alpha=200, sh_off=(0, 6), track=0, key=None):
    k = (text, key or id(f), fill, stroke, shadow, sh_alpha, track)
    if k in _wc: return _wc[k]
    pad = stroke + shadow * 2 + 14
    width = tw(text, f, track); asc, desc = f.getmetrics(); hh = asc + desc
    w = int(math.ceil(width)) + 2 * pad; h = hh + 2 * pad
    if shadow:
        sh = Image.new('L', (w, h), 0)
        _draw(ImageDraw.Draw(sh), (pad + sh_off[0], pad + sh_off[1]), text, f, 255, stroke, track, 255)
        sh = sh.filter(ImageFilter.GaussianBlur(shadow))
        a = np.clip(np.array(sh).astype(np.float32) * (sh_alpha / 255.0) * 1.7, 0, 255).astype(np.uint8)
        im = Image.fromarray(np.dstack([np.zeros_like(a)] * 3 + [a]), 'RGBA')
    else:
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    top = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    _draw(ImageDraw.Draw(top), (pad, pad), text, f, fill + (255,), stroke, track, (0, 0, 0, 255))
    im = Image.alpha_composite(im, top)
    r = (np.array(im), pad, width, hh); _wc[k] = r; return r


def fit(lines, path, size, maxw=900, wght=None, track=0):
    while True:
        f = font(path, size, wght); sp = f.getlength(' ')
        mw = 0
        for ln in lines:
            ts = [t if isinstance(t, str) else t[0] for t in ln]
            mw = max(mw, sum(tw(t, f, track) for t in ts) + sp * (len(ts) - 1))
        if mw <= maxw or size < 30: return f, size
        size -= 4


def layout(lines, f, cx, cy, fill=WHITE, stroke=0, shadow=14, track=0, lh=None, sh_alpha=200, key=None):
    asc, desc = f.getmetrics(); lh = lh or int((asc + desc) * 1.0)
    sp = f.getlength(' ') + track
    y0 = cy - lh * len(lines) / 2.0; out = []
    for li, ln in enumerate(lines):
        toks = [(t, fill) if isinstance(t, str) else t for t in ln]
        ws = [tw(t, f, track) for t, _ in toks]
        x = cx - (sum(ws) + sp * (len(toks) - 1)) / 2.0
        for (t, col), wd in zip(toks, ws):
            a, pad, width, hh = word_img(t, f, col, stroke=stroke, shadow=shadow, track=track, sh_alpha=sh_alpha, key=key)
            wx = x - pad; wy = y0 + li * lh + (lh - hh) / 2.0 - pad
            out.append(dict(a=a, cx=wx + a.shape[1] / 2.0, cy=wy + a.shape[0] / 2.0))
            x += wd + sp
    return out


def comp(fr, L, op=1.0, dx=0, dy=0, sc=1.0):
    if op <= 0.003: return
    img = L['a']
    if abs(sc - 1.0) > 0.004:
        img = cv2.resize(img, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
    h, w = img.shape[:2]
    x = int(round(L['cx'] + dx - w / 2.0)); y = int(round(L['cy'] + dy - h / 2.0))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    sub = img[y0 - y:y1 - y, x0 - x:x1 - x]
    a = sub[..., 3:4].astype(np.float32) * (op / 255.0)
    reg = fr[y0:y1, x0:x1].astype(np.float32)
    fr[y0:y1, x0:x1] = (reg + (sub[..., :3].astype(np.float32) - reg) * a).astype(np.uint8)


def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def eo(p): return 1 - (1 - clamp(p)) ** 3
def eio(p):
    p = clamp(p); return 3 * p * p - 2 * p * p * p


class Block:
    """words appear one by one at their spoken time; whole block leaves at t_out"""
    def __init__(self, words, times, t_out, style='slam', d=None, fo=0.14):
        self.w, self.t, self.t_out, self.style, self.fo = words, times, t_out, style, fo
        self.d = d or (0.13 if style == 'slam' else 0.34)

    def draw(self, fr, t):
        if t < self.t[0] or t > self.t_out + self.fo: return
        ko = 1.0 if t <= self.t_out else 1 - (t - self.t_out) / self.fo
        for L, t0 in zip(self.w, self.t):
            if t < t0: continue
            p = clamp((t - t0) / self.d)
            if self.style == 'slam': comp(fr, L, min(1, p * 1.6) * ko, 0, 0, 1 + 0.20 * (1 - eo(p)))
            else: comp(fr, L, eo(p) * ko, 0, 14 * (1 - eo(p)))


def panel(w, h, cx, cy, draw_fn, fill=(10, 10, 14, 222), outline=(255, 255, 255, 46), radius=28, bar=None):
    pad = 40
    im = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('L', im.size, 0); ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 10, pad + w, pad + h + 10), radius, fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(18)); a = np.array(sh)
    im = Image.fromarray(np.dstack([np.zeros_like(a)] * 3 + [a]), 'RGBA')
    top = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(top)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), radius, fill=fill, outline=outline, width=2)
    if bar: d.rounded_rectangle((pad, pad + 26, pad + 8, pad + h - 26), 4, fill=bar + (255,))
    draw_fn(d, pad, pad)
    im = Image.alpha_composite(im, top)
    return dict(a=np.array(im), cx=cx, cy=cy)


def wrap(text, f, maxw):
    out, cur = [], ''
    for wd in text.split():
        t = (cur + ' ' + wd).strip()
        if f.getlength(t) <= maxw: cur = t
        else: out.append(cur); cur = wd
    out.append(cur); return out


class Still:
    def __init__(self, path, soften=1.4, crop=None, prep=None):
        im = Image.open(path).convert('RGB')
        if crop: im = im.crop(crop)
        a = np.array(im)
        if prep: a = prep(a)
        r = max(1350 / a.shape[1], 2400 / a.shape[0])
        a = cv2.resize(a, (int(a.shape[1] * r + 0.5), int(a.shape[0] * r + 0.5)), interpolation=cv2.INTER_LANCZOS4)
        y = (a.shape[0] - 2400) // 2; x = (a.shape[1] - 1350) // 2
        a = a[y:y + 2400, x:x + 1350]
        if soften: a = cv2.GaussianBlur(a, (0, 0), soften)
        self.a = np.ascontiguousarray(a)

    def frame(self, z=1.0, px=0.0, py=0.0, bright=1.0):
        k = max(z, 1.0) / 1.25
        hw, hh = W / (2 * k), H / (2 * k)
        cx = 675 + px * (675 - hw); cy = 1200 + py * (1200 - hh)
        M = np.float32([[k, 0, W / 2 - k * cx], [0, k, H / 2 - k * cy]])
        f = cv2.warpAffine(self.a, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if bright != 1.0: f = cv2.convertScaleAbs(f, alpha=bright, beta=0)
        return f


class Vid:
    def __init__(self, path, ss=0.0):
        self.p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-ss', str(ss), '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
        self.last = np.zeros((H, W, 3), np.uint8)

    def read(self):
        b = self.p.stdout.read(W * H * 3)
        if len(b) == W * H * 3: self.last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        return self.last

    def close(self):
        try: self.p.kill()
        except Exception: pass


def vignette(strength=0.62, power=2.2, scan=False, band=None):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 1.4142
    m = 1 - strength * np.clip(r, 0, 1) ** power
    if band:  # (cy, sigma, depth) darker band behind text
        cy, sg, dp = band
        m *= 1 - dp * np.exp(-((yy - cy) ** 2) / (2 * sg * sg))
    if scan: m[::4, :] *= 0.86; m[1::4, :] *= 0.95
    m8 = np.clip(m * 255, 0, 255).astype(np.uint8)
    return np.ascontiguousarray(np.dstack([m8] * 3))


def mul(fr, m8):
    return cv2.multiply(fr, m8, scale=1 / 255.0)


_rng = np.random.default_rng(7)
_G = []
for _i in range(6):
    n = _rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)
    _G.append(n)


def grain(fr, i, amt=9.0):
    n = _G[i % len(_G)] * amt
    pos = np.clip(n, 0, 255).astype(np.uint8); neg = np.clip(-n, 0, 255).astype(np.uint8)
    pos = cv2.merge([pos] * 3); neg = cv2.merge([neg] * 3)
    return cv2.subtract(cv2.add(fr, pos), neg)


def glitch(fr, k, seed):
    r = np.random.default_rng(seed); out = fr.copy()
    for _ in range(int(4 + 8 * k)):
        y = int(r.integers(0, H - 60)); h = int(r.integers(10, 110)); dx = int(r.integers(-90, 90) * k)
        out[y:y + h] = np.roll(out[y:y + h], dx, axis=1)
    s = int(14 * k) + 2
    out[..., 0] = np.roll(out[..., 0], s, axis=1); out[..., 2] = np.roll(out[..., 2], -s, axis=1)
    return out


def writer(path):
    return subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                             '-c:v', 'libx264', '-crf', '17', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', str(FPS), path], stdin=subprocess.PIPE)


BRAND_F = font(POP, 36)
BRAND = layout([['BLESSED PRAYERS']], BRAND_F, W / 2, 232, fill=(255, 255, 255), shadow=10, track=7, sh_alpha=170)


def brand(fr, op=0.72):
    for L in BRAND: comp(fr, L, op)
