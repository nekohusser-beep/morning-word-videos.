#!/usr/bin/env python3
"""Seamless 30 s animated night scene (stars, Milky Way, morphing wisps, mountains, burning bush, embers).
Usage: render_scene.py test OUTDIR      -> a few JPG test frames
       render_scene.py loop OUT.mp4      -> 30 s seamless loop, 1920x1080, 24 fps
Free: numpy + PIL + ffmpeg only."""
import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw

W, H = 2112, 1188          # internal canvas (10% margin for camera drift)
OW, OH = 1920, 1080
FPS, T = 24, 30.0
NF = int(FPS * T)
rs = np.random.default_rng(11)
F32 = np.float32
SHOOT = False              # calm loop: no shooting star (it would repeat every 30 s)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def gfield(h, w, amp_exp, seed):
    r = np.random.default_rng(seed)
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1.0
    spec = (r.normal(size=(h, w)) + 1j * r.normal(size=(h, w))) / f ** amp_exp
    spec[0, 0] = 0
    a = np.fft.ifft2(spec).real
    a = (a - a.mean()) / a.std()
    return a.astype(F32)


def up(a, w, h):
    return np.asarray(Image.fromarray(a.astype(F32), mode="F").resize((w, h), Image.BICUBIC), dtype=F32)


def ridge1d(n, amp_exp, seed):
    r = np.random.default_rng(seed)
    f = np.fft.rfftfreq(n)
    f[0] = 1
    spec = (r.normal(size=f.size) + 1j * r.normal(size=f.size)) / f ** amp_exp
    spec[0] = 0
    a = np.fft.irfft(spec, n)
    return ((a - a.mean()) / a.std()).astype(F32)


xs = np.arange(W, dtype=F32)[None, :]
ys = np.arange(H, dtype=F32)[:, None]

# ---------------------------------------------------------------- sky
top = np.array([4, 6, 20], F32) / 255
mid = np.array([11, 19, 54], F32) / 255
hor = np.array([52, 58, 108], F32) / 255
yy = (ys / H)[:, :, None]
s1 = smooth(yy / 0.66)
s2 = smooth((yy - 0.46) / 0.30) ** 1.6
sky = (top + (mid - top) * s1)
sky = sky + (hor - sky) * s2
sky = np.broadcast_to(sky, (H, W, 3)).copy()

# Milky Way band
alpha_ang = -0.42
nx, ny = -math.sin(alpha_ang), math.cos(alpha_ang)
cx, cy = 0.52 * W, 0.34 * H
u = (xs - cx) * nx + (ys - cy) * ny
band = np.exp(-(u / (0.12 * H)) ** 2).astype(F32)
core = np.exp(-(u / (0.045 * H)) ** 2).astype(F32)
n1 = up(gfield(297, 528, 1.25, 3), W, H)
n2 = up(gfield(297, 528, 1.6, 4), W, H)
detail = np.clip(0.55 + 0.35 * n1, 0, 1.3) ** 1.4
dust = smooth((n2 - 0.1) / 1.2) * core * 0.85
mw = (band * (0.18 + 0.75 * detail) + core * 0.35) * (1 - dust)
mwcol = np.array([0.50, 0.58, 0.90], F32)
sky += (mw[:, :, None] * mwcol[None, None, :]) * 0.50
# faint warm glow on the horizon behind the bush side
hx = np.exp(-((xs - 0.64 * W) / (0.42 * W)) ** 2) * np.exp(-((ys - 0.78 * H) / (0.16 * H)) ** 2)
sky += hx[:, :, None] * np.array([0.22, 0.10, 0.07], F32) * 0.55

# ---------------------------------------------------------------- stars
NS = 2600
acc = []
while len(acc) < NS:
    x = rs.random() * W
    y = rs.random() * 0.70 * H
    uu = (x - cx) * nx + (y - cy) * ny
    p = 0.22 + 1.6 * math.exp(-(uu / (0.14 * H)) ** 2)
    if rs.random() < p / 1.82:
        acc.append((x, y))
sx = np.array([a[0] for a in acc]).astype(int)
sy = np.array([a[1] for a in acc]).astype(int)
sb = (0.10 + 0.90 * rs.random(NS) ** 6).astype(F32)
st = rs.random(NS).astype(F32)
scol = (np.array([0.78, 0.86, 1.0], F32)[None, :] * (1 - st[:, None]) + np.array([1.0, 0.90, 0.74], F32)[None, :] * st[:, None])
samp = (0.15 + 0.40 * rs.random(NS)).astype(F32)
sk = rs.integers(2, 11, NS)
sph = (rs.random(NS) * 2 * math.pi).astype(F32)
bright_idx = np.where(sb > 0.30)[0]
spr = np.zeros((9, 9), F32)
for j in range(9):
    for i in range(9):
        spr[j, i] = math.exp(-(((i - 4) ** 2 + (j - 4) ** 2) / (2 * 1.15 ** 2)))


def add_stars(img, t):
    tw = 1 - samp * 0.5 + samp * 0.5 * np.sin(2 * math.pi * sk * t / T + sph)
    inten = sb * tw
    dim = np.where(sb <= 0.30)[0]
    m = inten[dim, None] * scol[dim] * 0.9
    ok = (sx[dim] > 0) & (sx[dim] < W - 1) & (sy[dim] > 0) & (sy[dim] < H - 1)
    d = dim[ok]
    np.add.at(img, (sy[d], sx[d]), m[ok])
    np.add.at(img, (sy[d], sx[d] + 1), m[ok] * 0.35)
    for i in bright_idx:
        x, y = sx[i], sy[i]
        if 5 < x < W - 5 and 5 < y < H - 5:
            img[y - 4:y + 5, x - 4:x + 5] += (spr * inten[i] * 1.6)[:, :, None] * scol[i][None, None, :]
    return img


# ---------------------------------------------------------------- wisps / fog fields
CA = gfield(297, 528, 1.35, 21)
CB = gfield(297, 528, 1.35, 22)
FA = gfield(149, 528, 1.5, 23)
FB = gfield(149, 528, 1.5, 24)
wprof = (smooth((ys / H - 0.06) / 0.22) * (1 - smooth((ys / H - 0.42) / 0.20)))[:, :, None].astype(F32)
fogprof1 = np.exp(-((ys - 0.655 * H) / (0.045 * H)) ** 2).astype(F32)
fogprof2 = np.exp(-((ys - 0.775 * H) / (0.05 * H)) ** 2).astype(F32)

# ---------------------------------------------------------------- mountains / ground
def layer(yb, amp, exp, seed, bump=None):
    r = ridge1d(W, exp, seed) * amp
    base = yb + r
    if bump is not None:
        bx, bw, bh = bump
        base = base - bh * np.exp(-((np.arange(W) - bx) / bw) ** 2)
    a = np.clip((ys - base[None, :]) / 1.6 + 0.5, 0, 1).astype(F32)
    return a, base


far_a, _ = layer(0.600 * H, 0.050 * H, 1.55, 31)
mid_a, _ = layer(0.665 * H, 0.060 * H, 1.5, 32)
near_a, _ = layer(0.740 * H, 0.050 * H, 1.45, 33)
BX = int(0.64 * W)
gr_a, gr_base = layer(0.865 * H, 0.020 * H, 1.3, 34, bump=(BX, 0.16 * W, 0.060 * H))
far_col = (np.array([30, 36, 76], F32) / 255)[None, None, :] * (1 - 0.45 * ((ys / H - 0.60) / 0.2).clip(0, 1))[:, :, None]
mid_col = (np.array([17, 21, 50], F32) / 255)[None, None, :] * np.ones((H, 1, 1), F32)
near_col = (np.array([9, 11, 28], F32) / 255)[None, None, :] * np.ones((H, 1, 1), F32)
gr_col = (np.array([5, 5, 11], F32) / 255)[None, None, :] * np.ones((H, 1, 1), F32)

# ---------------------------------------------------------------- bush
bush_x = BX
bush_y = int(gr_base[BX]) + 8           # trunk base sits on the mound
BWIN, BHIN = 560, 460
SS = 2
bm = Image.new("L", (BWIN * SS, BHIN * SS), 0)
bd = ImageDraw.Draw(bm)
br = np.random.default_rng(5)


def branch(x, y, ang, ln, wd, depth):
    if depth == 0 or ln < 5:
        return
    ang = float(np.clip(ang, 0.50, math.pi - 0.50))   # branches reach up and out, never droop
    x2 = x + math.cos(ang) * ln
    y2 = y - math.sin(ang) * ln
    bd.line([(x, y), (x2, y2)], fill=255, width=max(2, int(wd * SS)))
    if depth <= 3:
        r_ = br.uniform(3.0, 6.5) * SS
        bd.ellipse([x2 - r_, y2 - r_ * 0.8, x2 + r_, y2 + r_ * 0.8], fill=255)
    for _ in range(2 if depth > 3 else 3):
        branch(x2, y2, ang + br.normal(0, 0.62), ln * br.uniform(0.62, 0.80), wd * 0.70, depth - 1)


for a0 in np.linspace(0.90, 2.25, 8):
    branch(BWIN * SS / 2 + br.uniform(-20, 20), BHIN * SS - 30, a0 + br.normal(0, 0.08), 84 * SS, 7.0, 7)
bmask = np.asarray(bm.resize((BWIN, BHIN), Image.LANCZOS), dtype=F32) / 255.0
bx0 = bush_x - BWIN // 2
by0 = bush_y - BHIN + 30
gy_, gx_ = np.mgrid[0:BHIN, 0:BWIN].astype(F32)
cxb, cyb = BWIN / 2, BHIN * 0.60      # glow centre inside the window
# ember particles
NE = 120
er = np.random.default_rng(9)
e_x0 = er.normal(0, 55, NE)
e_k = er.choice([4, 5, 6, 7], NE)
e_ph = er.random(NE)
e_rise = er.uniform(380, 700, NE)
e_wob = er.uniform(10, 34, NE)
e_wm = er.integers(2, 9, NE)
e_wp = er.random(NE) * 6.28
e_drift = er.uniform(-40, 90, NE)
e_sig = er.uniform(1.2, 2.3, NE)

ESP = 13
espr = np.zeros((ESP, ESP), F32)
for j in range(ESP):
    for i in range(ESP):
        espr[j, i] = math.exp(-(((i - 6) ** 2 + (j - 6) ** 2) / (2 * 1.7 ** 2)))


def flick(t, ph=0.0):
    return (1 + 0.10 * math.sin(2 * math.pi * 47 * t / T + ph) + 0.07 * math.sin(2 * math.pi * 83 * t / T + 1.3 + ph)
            + 0.05 * math.sin(2 * math.pi * 131 * t / T + 2.1 + ph) + 0.04 * math.sin(2 * math.pi * 11 * t / T + 0.4))


# flame tongues
NT = 15
tr = np.random.default_rng(17)
t_dx = tr.uniform(-78, 78, NT)
t_h = tr.uniform(120, 215, NT)
t_w = tr.uniform(10, 19, NT)
t_k = tr.integers(40, 120, NT)
t_ph = tr.random(NT) * 6.28
t_sw = tr.integers(5, 14, NT)


FBASE = cyb + 78


def flame_layer(t):
    """returns warm additive RGB for the bush window (BHIN, BWIN, 3): tapered tongues that lick and sway"""
    I = np.zeros((BHIN, BWIN), F32)
    for j in range(NT):
        fl = 0.74 + 0.26 * math.sin(2 * math.pi * t_k[j] * t / T + t_ph[j])
        hh = t_h[j] * (0.92 + 0.16 * fl) * 1.15
        rel = np.clip((FBASE - gy_) / hh, 0, 1.0)
        inside = (np.clip((FBASE + 55 - gy_) / 90.0, 0, 1) ** 1.3) * (gy_ >= FBASE - hh)   # soft root, no hard base line
        wob = 20 * rel ** 1.3 * np.sin(2 * math.pi * t_sw[j] * t / T + t_ph[j] + rel * 3.2)
        w = t_w[j] * 1.5 * (1 - 0.78 * rel ** 0.85) + 2.5
        dx = gx_ - (cxb + t_dx[j] + wob)
        I += np.exp(-(dx / w) ** 2) * (1 - rel) ** 1.15 * inside * fl * 0.62
    Ic = np.clip(I, 0, None)
    ramp = np.stack([np.clip(Ic * 1.5, 0, 1.3), (Ic ** 1.45) * 0.78, (np.clip(Ic - 0.45, 0, None) ** 1.8) * 0.9], -1)
    return ramp


# ---------------------------------------------------------------- camera / post
vig = (1 - 0.42 * (((xs - 0.5 * W) / (0.60 * W)) ** 2 + ((ys - 0.5 * H) / (0.62 * H)) ** 2)).clip(0.35, 1)[:, :, None].astype(F32)
dither_pool = [((np.random.default_rng(100 + i).random((H, W, 1)) - 0.5) * (1.6 / 255)).astype(F32) for i in range(6)]
warm = np.array([1.0, 0.52, 0.18], F32)


def frame(t):
    th = 2 * math.pi * t / T
    img = sky.copy()
    add_stars(img, t)
    # shooting star, once per loop
    ts = t - 19.0
    if SHOOT and 0 <= ts < 1.3:
        p = ts / 1.3
        hx0, hy0 = 0.20 * W + p * 0.26 * W, 0.10 * H + p * 0.17 * H
        for k in range(46):
            q = k / 46.0
            px = int(hx0 - q * 0.075 * W)
            py = int(hy0 - q * 0.049 * H)
            if 1 < px < W - 2 and 1 < py < H - 2:
                img[py - 1:py + 2, px - 1:px + 2] += (1 - q) ** 2 * math.sin(math.pi * p) * 0.9 * np.array([0.9, 0.95, 1.0], F32)
    # wisps
    wf = up(CA * math.cos(th) + CB * math.sin(th), W, H)
    wa = (smooth((wf - 0.25) / 1.4) ** 1.5)[:, :, None] * wprof * 0.30
    img = img + wa * np.array([0.26, 0.31, 0.52], F32)
    # fire light (wide + tight), flicker
    fl = flick(t)
    Lw = (np.exp(-((xs - bush_x) ** 2) / (2 * 520.0 ** 2)) * np.exp(-((ys - (bush_y - 120)) ** 2) / (2 * 380.0 ** 2))).astype(F32) * fl
    Lt = (np.exp(-((xs - bush_x) ** 2) / (2 * 190.0 ** 2)) * np.exp(-((ys - (bush_y - 140)) ** 2) / (2 * 150.0 ** 2))).astype(F32) * fl
    # far / mid mountains
    a = far_a[:, :, None]
    img = img * (1 - a) + (far_col + Lw[:, :, None] * warm * 0.035) * a
    ff = up(FA * math.cos(th) + FB * math.sin(th), W, H)
    fg1 = (smooth((ff + 0.1) / 1.6) * fogprof1)[:, :, None] * 0.34
    img = img + fg1 * np.array([0.20, 0.24, 0.42], F32) * (1 - 0.0)
    a = mid_a[:, :, None]
    img = img * (1 - a) + (mid_col + Lw[:, :, None] * warm * 0.07) * a
    ff2 = up(FB * math.cos(th + 1.7) + FA * math.sin(th + 1.7), W, H)
    fg2 = (smooth((ff2 + 0.15) / 1.6) * fogprof2)[:, :, None] * 0.38
    img = img + fg2 * (np.array([0.16, 0.19, 0.34], F32) + Lw[:, :, None] * warm * 0.35)
    a = near_a[:, :, None]
    img = img * (1 - a) + (near_col + Lw[:, :, None] * warm * 0.12) * a
    # ground
    a = gr_a[:, :, None]
    img = img * (1 - a) + (gr_col + (Lw[:, :, None] * 0.55 + Lt[:, :, None] * 1.0) * warm * 0.42) * a
    # warm glow + flame behind the bush
    glow = (np.exp(-((xs - bush_x) ** 2) / (2 * 120.0 ** 2)) * np.exp(-((ys - (bush_y - 150)) ** 2) / (2 * 120.0 ** 2))).astype(F32) * fl
    img += glow[:, :, None] * np.array([0.95, 0.42, 0.10], F32) * 0.55
    img += Lt[:, :, None] * np.array([0.8, 0.34, 0.08], F32) * 0.22
    fire = flame_layer(t) * fl
    ys0, xs0 = max(by0, 0), max(bx0, 0)
    img[by0:by0 + BHIN, bx0:bx0 + BWIN] += fire
    # bush silhouette in front, edges lit
    M = bmask[:, :, None]
    lit = np.clip(((fire.sum(-1)) * 0.9)[:, :, None], 0, 1)
    bush_col = np.array([0.07, 0.035, 0.02], F32) + lit * np.array([1.0, 0.48, 0.12], F32) * 0.55
    reg = img[by0:by0 + BHIN, bx0:bx0 + BWIN]
    img[by0:by0 + BHIN, bx0:bx0 + BWIN] = reg * (1 - M * 0.92) + bush_col * M * 0.92
    # embers
    for i in range(NE):
        fr = (e_ph[i] + e_k[i] * t / T) % 1.0
        ex = bush_x + e_x0[i] * (0.6 + 0.4 * fr) + e_wob[i] * math.sin(2 * math.pi * e_wm[i] * t / T + e_wp[i]) + e_drift[i] * fr
        ey = bush_y - 150 - e_rise[i] * fr
        al = math.sin(math.pi * min(1.0, fr * 1.15)) ** 0.8 * (1 - fr) ** 0.5
        ix, iy = int(ex), int(ey)
        if 8 < ix < W - 8 and 8 < iy < H - 8 and al > 0.02:
            c = (1.0 - 0.0 * fr, 0.80 - 0.50 * fr, 0.34 - 0.26 * fr)
            sc = al * (0.65 + 0.35 * math.sin(7 * t + i)) * (e_sig[i] / 1.7) * 1.25
            img[iy - 6:iy + 7, ix - 6:ix + 7] += espr[:, :, None] * np.array(c, F32)[None, None, :] * sc
    img *= vig
    img += dither_pool[int(t * FPS) % 6]
    # tone / highlight roll-off
    over = np.clip(img - 0.82, 0, None)
    img = np.where(img > 0.82, 0.82 + 0.18 * np.tanh(over / 0.18), img)
    out = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
    # camera: gentle breathing zoom + sway, loops seamlessly
    z = 0.030 * (0.5 - 0.5 * math.cos(th))
    cw = W / (1 + z)
    ch = H / (1 + z)
    mx, my = (W - cw) / 2, (H - ch) / 2
    px = mx * (0.9 * math.sin(th + 0.4))
    py = my * (0.7 * math.sin(2 * th + 1.0))
    x0 = (W - cw) / 2 + px
    y0 = (H - ch) / 2 + py
    return Image.fromarray(out).resize((OW, OH), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "test":
        import os
        od = sys.argv[2]
        os.makedirs(od, exist_ok=True)
        for tt in [0.0, 9.0, 20.0]:
            frame(tt).resize((1280, 720), Image.LANCZOS).save(f"{od}/t{int(tt):02d}.jpg", quality=90)
            print("saved", tt, flush=True)
    elif mode == "bench":
        import time
        t0 = time.time()
        for i in range(12):
            frame(i / FPS)
        print("sec/frame", (time.time() - t0) / 12)
    else:
        # part START END OUT : frames [START, END) of the loop, to run two halves in parallel
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        pr = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-g", "48", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for i in range(a, b):
            pr.stdin.write(frame(i / FPS).tobytes())
            if (i - a) % 60 == 0:
                print("frame", i, "/", b, flush=True)
        pr.stdin.close()
        pr.wait()
        print("done", out)
