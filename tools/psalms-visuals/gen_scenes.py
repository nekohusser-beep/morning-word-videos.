#!/usr/bin/env python3
"""Procedural calm dim scenes for the Psalms 1-150 sleep video. No text, no people, no brands."""
import sys, math, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

W, H = 1920, 1080
S = 0.5  # work at half res for the soft layers, upscale (soft = fine)

def rgb(h):
    h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], np.float32) / 255.0

def vgrad(stops, h=H, w=W):
    ys = np.linspace(0, 1, h, dtype=np.float32)
    pos = [p for p, _ in stops]; cols = np.stack([c for _, c in stops])
    out = np.stack([np.interp(ys, pos, cols[:, k]) for k in range(3)], -1)
    return np.repeat(out[:, None, :], w, axis=1)

def noise1d(n, rng, octaves=5, pers=0.5, base=3):
    out = np.zeros(n, np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        k = base * 2 ** o + 1
        pts = rng.random(k)
        out += amp * np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)
        tot += amp; amp *= pers
    out /= tot
    return out

def noise2d(h, w, scale, rng, octaves=4, pers=0.5):
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        s = max(2, int(scale / 2 ** o))
        gh, gw = max(2, h // s + 2), max(2, w // s + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        z = ndi.zoom(g, (h / (gh - 1), w / (gw - 1)), order=3)[:h, :w]
        if z.shape != (h, w):
            z = np.pad(z, ((0, h - z.shape[0]), (0, w - z.shape[1])), mode='edge')
        out += amp * z; tot += amp; amp *= pers
    out /= tot
    return (out - out.min()) / (out.max() - out.min() + 1e-6)

def blur(a, s):
    if a.ndim == 3:
        return np.stack([ndi.gaussian_filter(a[..., k], s) for k in range(3)], -1)
    return ndi.gaussian_filter(a, s)

def lum(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722

def mask_below(ridge_y, soft=1.5):
    """HxW mask: 1 below the ridge line (ridge_y per column)."""
    yy = np.arange(H, dtype=np.float32)[:, None]
    m = np.clip((yy - ridge_y[None, :]) / soft + 0.5, 0, 1)
    return m

def comp(base, color, mask):
    m = mask[..., None] if mask.ndim == 2 else mask
    return base * (1 - m) + color * m

def hills(base, rng, layers, horizon, sky_ref, haze, dark, amp=120, rough=0.55, snow=None):
    """layers hills from far to near; colour blends from haze (far) to dark (near)."""
    img = base
    for i in range(layers):
        t = i / max(1, layers - 1)
        y0 = horizon + t * (H - horizon) * 0.55 + rng.random() * 25
        a = amp * (1.0 - 0.5 * t) * (0.7 + 0.6 * rng.random())
        r = y0 - a * (noise1d(W, rng, 5, rough, 2 + i % 3) - 0.5) * 2
        col = haze * (1 - t) + dark * t
        m = mask_below(r, 2.0)
        # atmospheric gradient on each hill: lighter toward its top edge
        yy = np.arange(H, dtype=np.float32)[:, None]
        g = np.clip(1 - (yy - r[None, :]) / 260.0, 0, 1)[..., None]
        c = col[None, None, :] * (1 + 0.35 * (1 - t) * g)
        img = comp(img, c, m)
    return img

def stars(img, rng, n, maxy, bright=0.9, big=0.04, tint=(1.0, 1.0, 1.0)):
    layer = np.zeros((H, W), np.float32)
    xs = rng.integers(0, W, n); ys = (rng.random(n) ** 1.3 * maxy).astype(int)
    br = rng.random(n) ** 3.0 * bright + 0.12
    bigmask = rng.random(n) < big
    layer[ys, xs] = br
    bigl = np.zeros((H, W), np.float32)
    bigl[ys[bigmask], xs[bigmask]] = br[bigmask]
    core = layer.copy()
    soft = ndi.gaussian_filter(bigl, 1.6) * 9
    sm = ndi.gaussian_filter(core, 0.7) * 2.2
    layer = np.clip(sm + soft, 0, 1)
    # fade near horizon
    fade = np.clip(1 - np.arange(H)[:, None] / (maxy * 1.05), 0, 1) ** 0.6
    layer *= fade
    return img + layer[..., None] * np.array(tint, np.float32)[None, None, :]

def moon(img, cx, cy, r, glow=0.25, col=(1.0, 0.96, 0.85), crescent=False, intensity=0.85):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    disc = np.clip((r - d) / 1.8 + 0.5, 0, 1)
    if crescent:
        d2 = np.sqrt((xx - cx - r * 0.55) ** 2 + (yy - cy + r * 0.1) ** 2)
        disc *= 1 - np.clip((r * 0.95 - d2) / 1.8 + 0.5, 0, 1)
    halo = np.exp(-(d / (r * 5.0)) ** 1.6) * glow
    c = np.array(col, np.float32)
    return img + disc[..., None] * c * intensity + halo[..., None] * c * 0.6

def mist(img, rng, y0, y1, col, strength=0.35, scale=300):
    n = noise2d(H, W, scale, rng, 4)
    yy = np.arange(H, dtype=np.float32)[:, None]
    band = np.exp(-((yy - (y0 + y1) / 2) / ((y1 - y0) / 2.2)) ** 2)
    m = (band * (0.35 + 0.8 * n) * strength)[..., None]
    return img * (1 - m) + np.array(col, np.float32)[None, None, :] * m

def tree_layer(img, rng, ridge, color, n, hmin, hmax, kind='cedar', width=0.38):
    """silhouette trees planted on a ridge (array of y per column)."""
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    xs = np.sort(rng.integers(20, W - 20, n))
    for x in xs:
        base = ridge[x] + 6
        h = rng.uniform(hmin, hmax); w = h * width
        if kind == 'cedar':
            tiers = 7
            d.polygon([(x - 2, base), (x + 2, base), (x + 1.5, base - h), (x - 1.5, base - h)], fill=255)
            for t in range(tiers):
                f = t / tiers
                yb = base - h * (0.12 + 0.82 * f)
                ww = w * (1 - f) ** 0.9 * 0.5 + 3
                d.polygon([(x - ww, yb + h * 0.07), (x, yb - h * 0.16), (x + ww, yb + h * 0.07)], fill=255)
        elif kind == 'pine':
            d.polygon([(x - w / 2, base), (x, base - h), (x + w / 2, base)], fill=255)
        elif kind == 'round':
            d.rectangle([x - 2, base - h * 0.35, x + 2, base], fill=255)
            d.ellipse([x - w * 0.55, base - h, x + w * 0.55, base - h * 0.3], fill=255)
    m = np.asarray(im, np.float32) / 255.0
    m = ndi.gaussian_filter(m, 0.8)
    return comp(img, np.array(color, np.float32)[None, None, :], m)

def finish(img, rng, target_mean, accents=None, grain=0.8):
    img = np.clip(img, 0, 1)
    m = lum(img).mean() * 255
    if m > 0:
        k = target_mean / m
        img = np.clip(img * min(k, 3.0), 0, 1)
    if accents is not None:
        img = np.clip(img + accents, 0, 1)
    # vignette (soft)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.28 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.0 / 2
    img = img * v[..., None]
    out = img * 255.0 + rng.normal(0, grain, img.shape).astype(np.float32)
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), 'RGB')

# ---------------- scene kinds ----------------
def sky(stops):
    return vgrad(stops)

def k_night_hills(rng, P):
    base = sky([(0, rgb(P['top'])), (0.55, rgb(P['mid'])), (1, rgb(P['hor']))])
    hor = int(H * rng.uniform(0.52, 0.62))
    img = hills(base, rng, 5, hor, None, rgb(P['haze']), rgb(P['dark']), amp=rng.uniform(70, 150))
    img = mist(img, rng, hor - 40, hor + 160, rgb(P['haze']) * 1.1, 0.35)
    acc = np.zeros((H, W, 3), np.float32)
    acc = stars(acc, rng, int(rng.integers(500, 1400)), hor, 0.85, 0.05, P.get('startint', (0.9, 0.95, 1.0)))
    if P.get('moon'):
        mx, my = rng.uniform(0.18, 0.82) * W, rng.uniform(0.14, 0.32) * H
        acc = moon(acc, mx, my, rng.uniform(26, 44), 0.20, crescent=P.get('crescent', False))
    return img, acc

def k_dawn(rng, P):
    base = sky([(0, rgb(P['top'])), (0.35, rgb(P['mid'])), (0.62, rgb(P['hor'])), (1, rgb(P['hor']) * 0.7)])
    hor = int(H * rng.uniform(0.58, 0.66))
    # sun glow
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    sx = rng.uniform(0.25, 0.75) * W
    d = np.sqrt(((xx - sx) / 1.6) ** 2 + (yy - hor) ** 2)
    glow = np.exp(-(d / 330.0) ** 1.4)[..., None] * rgb(P['glow'])[None, None, :] * 0.9
    base = base + glow
    img = hills(base, rng, 4, hor, None, rgb(P['haze']), rgb(P['dark']), amp=rng.uniform(60, 110))
    img = mist(img, rng, hor - 20, hor + 130, rgb(P['hor']) * 0.9, 0.5, 260)
    acc = np.zeros((H, W, 3), np.float32)
    acc = stars(acc, rng, 220, int(hor * 0.55), 0.5)
    return img, acc

def k_water_moon(rng, P):
    hor = int(H * rng.uniform(0.5, 0.58))
    sk = sky([(0, rgb(P['top'])), (0.6, rgb(P['mid'])), (1, rgb(P['hor']))])
    top = sk[:hor + 1]
    img = np.zeros((H, W, 3), np.float32)
    img[:hor] = sk[:hor] if False else vgrad([(0, rgb(P['top'])), (0.7, rgb(P['mid'])), (1, rgb(P['hor']))], hor)
    # distant shore
    r = hor - 18 - 55 * (noise1d(W, rng, 5, 0.55, 3) - 0.3)
    img = comp(np.vstack([img[:hor], np.zeros((H - hor, W, 3), np.float32)]), rgb(P['dark']) * 1.3, mask_below(r, 2) * (np.arange(H)[:, None] < hor))
    mx = rng.uniform(0.25, 0.75) * W; my = rng.uniform(0.15, 0.3) * H
    # water: mirror sky above horizon
    water_h = H - hor
    refl = img[max(0, hor - water_h):hor][::-1]
    if refl.shape[0] < water_h:
        refl = np.vstack([refl, np.repeat(refl[-1:], water_h - refl.shape[0], 0)])
    ripple = ndi.gaussian_filter(rng.normal(0, 1, (water_h, W)).astype(np.float32), (0.8, 40))
    ripple = ripple / (np.abs(ripple).max() + 1e-6)
    shift = (ripple * 7).astype(int)
    idx = np.clip(np.arange(W)[None, :] + shift, 0, W - 1)
    refl = np.take_along_axis(refl, idx[..., None].repeat(3, 2), 1) * (0.55 + 0.25 * np.linspace(1, 0, water_h)[:, None, None]) * rgb(P['water'])[None, None, :] / 0.4
    refl = refl * (0.85 + 0.25 * ripple[..., None])
    img[hor:] = refl
    img = mist(img, rng, hor - 25, hor + 25, rgb(P['hor']) * 1.2, 0.5, 200)
    acc = np.zeros((H, W, 3), np.float32)
    acc = stars(acc, rng, 700, hor - 30, 0.8)
    acc = moon(acc, mx, my, rng.uniform(30, 46), 0.22, crescent=P.get('crescent', False))
    # moon path on the water
    yy = np.arange(hor, H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    wid = 18 + (yy - hor) * 0.22
    path = np.exp(-((xx - mx) / wid) ** 2) * (0.5 + 0.5 * ripple) * np.exp(-(yy - hor) / 420.0)
    acc[hor:] += (path[..., None] * np.array([1.0, 0.95, 0.8], np.float32)[None, None, :] * 0.26)
    return img, acc

def k_mist_mountains(rng, P):
    base = sky([(0, rgb(P['top'])), (0.5, rgb(P['mid'])), (1, rgb(P['hor']))])
    img = base
    n = 6
    for i in range(n):
        t = i / (n - 1)
        y0 = H * (0.38 + 0.42 * t)
        pk = noise1d(W, rng, 6, 0.62, 2 + i % 2)
        ridge_y = y0 - (pk - 0.2) * (240 - 120 * t)
        col = rgb(P['haze']) * (1 - t) + rgb(P['dark']) * t
        img = comp(img, col[None, None, :], mask_below(ridge_y, 2.0))
        img = mist(img, rng, y0 - 10, y0 + 140, rgb(P['haze']) * 1.15, 0.55 * (1 - 0.4 * t), 340)
    acc = np.zeros((H, W, 3), np.float32)
    acc = stars(acc, rng, 300, int(H * 0.35), 0.6)
    if P.get('moon'):
        acc = moon(acc, rng.uniform(0.2, 0.8) * W, rng.uniform(0.1, 0.22) * H, 30, 0.2)
    return img, acc

def k_cedars(rng, P):
    base = sky([(0, rgb(P['top'])), (0.5, rgb(P['mid'])), (0.75, rgb(P['hor'])), (1, rgb(P['hor']) * 0.6)])
    hor = int(H * 0.66)
    img = hills(base, rng, 3, hor - 30, None, rgb(P['haze']), rgb(P['dark']) * 1.2, amp=70)
    ridge = hor + 60 - 70 * (noise1d(W, rng, 5, 0.55, 2) - 0.4)
    img = comp(img, rgb(P['dark'])[None, None, :] * 0.9, mask_below(ridge, 2))
    img = tree_layer(img, rng, ridge, rgb(P['dark']) * 0.8, 36, 120, 260, 'cedar')
    ridge2 = ridge + 110
    img = comp(img, rgb(P['dark'])[None, None, :] * 0.6, mask_below(ridge2, 2))
    img = tree_layer(img, rng, ridge2, rgb(P['dark']) * 0.5, 14, 220, 420, 'cedar', 0.34)
    img = mist(img, rng, ridge.min() - 20, ridge.max() + 20, rgb(P['hor']) * 0.8, 0.28, 240)
    acc = np.zeros((H, W, 3), np.float32)
    acc = stars(acc, rng, 420, int(H * 0.42), 0.7)
    if P.get('moon'):
        acc = moon(acc, rng.uniform(0.15, 0.85) * W, rng.uniform(0.12, 0.28) * H, 30, 0.2, crescent=True)
    return img, acc

def k_dunes(rng, P):
    base = sky([(0, rgb(P['top'])), (0.45, rgb(P['mid'])), (0.62, rgb(P['hor'])), (1, rgb(P['hor']) * 0.8)])
    img = base
    n = 5
    for i in range(n):
        t = i / (n - 1)
        y0 = H * (0.56 + 0.34 * t)
        c = noise1d(W, rng, 3, 0.45, 1)
        ridge_y = y0 - (c - 0.5) * (130 - 40 * t)
        # lit side: gradient across each dune
        col = rgb(P['haze']) * (1 - t) + rgb(P['dark']) * t
        yy = np.arange(H, dtype=np.float32)[:, None]
        edge = np.clip(1 - (yy - ridge_y[None, :]) / (90 + 80 * t), 0, 1)[..., None]
        cc = col[None, None, :] * (0.8 + 0.7 * edge) + rgb(P['lit'])[None, None, :] * edge * 0.18 * (1 - t * 0.5)
        img = comp(img, cc, mask_below(ridge_y, 2.5))
    img = mist(img, rng, H * 0.58, H * 0.7, rgb(P['hor']), 0.3, 360)
    acc = np.zeros((H, W, 3), np.float32)
    acc = stars(acc, rng, 330, int(H * 0.45), 0.7)
    return img, acc

def k_milkyway(rng, P):
    base = vgrad([(0, rgb(P['top'])), (1, rgb(P['hor']))])
    n = noise2d(H, W, 220, rng, 5)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ang = rng.uniform(-0.55, 0.55)
    dist = ((xx - W / 2) * math.sin(ang) + (yy - H * 0.4) * math.cos(ang))
    band = np.exp(-(dist / (170 + 70 * rng.random())) ** 2)
    mw = band * (0.25 + 0.95 * n ** 1.5)
    img = base + mw[..., None] * rgb(P['mw'])[None, None, :] * 0.5
    hor = int(H * 0.8)
    ridge = hor - 60 * (noise1d(W, rng, 5, 0.6, 3) - 0.3)
    img = comp(img, rgb(P['dark'])[None, None, :] * 0.7, mask_below(ridge, 2))
    if P.get('trees'):
        img = tree_layer(img, rng, ridge, rgb(P['dark']) * 0.5, 28, 70, 190, 'pine')
    acc = np.zeros((H, W, 3), np.float32)
    acc = stars(acc, rng, 2600, hor, 0.8, 0.03, (0.95, 0.97, 1.0))
    # extra faint dust stars concentrated on band
    dust = (rng.random((H, W)) < (band * 0.02 * (n > 0.45))).astype(np.float32)
    acc += ndi.gaussian_filter(dust, 0.6)[..., None] * 1.8 * np.array([0.95, 0.96, 1.0], np.float32)[None, None, :] * (np.arange(H)[:, None, None] < hor)
    return img, acc

def k_clouds(rng, P):
    base = vgrad([(0, rgb(P['top'])), (0.5, rgb(P['mid'])), (0.8, rgb(P['hor'])), (1, rgb(P['hor']) * 0.5)])
    n = noise2d(H, W, 260, rng, 5)
    n2 = noise2d(H, W, 90, rng, 4)
    yy = np.arange(H, dtype=np.float32)[:, None]
    cl = np.clip((n - 0.48) * 3.2, 0, 1) * np.clip(1 - np.abs(yy - H * 0.45) / (H * 0.4), 0, 1)
    lit = np.clip(1 - np.abs(yy - H * 0.62) / (H * 0.45), 0, 1) * (0.6 + 0.6 * n2)
    ccol = rgb(P['cloud'])[None, None, :]
    img = base * (1 - cl[..., None] * 0.7) + ccol * (cl * lit)[..., None] * 0.9 + ccol * 0.2 * cl[..., None]
    hor = int(H * 0.8)
    ridge = hor - 50 * (noise1d(W, rng, 5, 0.55, 2) - 0.3)
    img = comp(img, rgb(P['dark'])[None, None, :] * 0.6, mask_below(ridge, 2))
    acc = np.zeros((H, W, 3), np.float32)
    acc = stars(acc, rng, 200, int(H * 0.3), 0.5)
    return img, acc

def k_sea(rng, P):
    hor = int(H * rng.uniform(0.5, 0.56))
    sk = vgrad([(0, rgb(P['top'])), (0.55, rgb(P['mid'])), (1, rgb(P['hor']))], hor)
    sea = vgrad([(0, rgb(P['hor']) * 0.9), (0.25, rgb(P['sea1'])), (1, rgb(P['sea2']))], H - hor)
    yy = np.arange(H - hor, dtype=np.float32)[:, None]
    rip = ndi.gaussian_filter(rng.normal(0, 1, (H - hor, W)).astype(np.float32), (0.7, 55))
    rip /= np.abs(rip).max() + 1e-6
    sea = sea * (1 + 0.16 * rip[..., None] * np.clip(yy / 200, 0.2, 1)[..., None])
    sx = rng.uniform(0.3, 0.7) * W
    xx = np.arange(W, dtype=np.float32)[None, :]
    glint = np.exp(-((xx - sx) / (60 + yy * 0.5)) ** 2) * np.exp(-yy / 380) * (0.45 + 0.7 * np.clip(rip, 0, 1))
    sea = sea + glint[..., None] * rgb(P['glow'])[None, None, :] * 0.5
    img = np.vstack([sk, sea])
    d = np.sqrt(((np.mgrid[0:H, 0:W][1] - sx) / 1.8) ** 2 + (np.mgrid[0:H, 0:W][0] - hor) ** 2)
    img[:hor] += (np.exp(-(d / 300.0) ** 1.3)[..., None] * rgb(P['glow'])[None, None, :] * 0.6)[:hor]
    if P.get('headland'):
        r = hor - 70 * np.clip(noise1d(W, rng, 4, 0.5, 1) - 0.6, 0, 1) * 2.4 - 3
        r[: int(W * 0.35)] = hor
        m = mask_below(r, 2) * (np.arange(H)[:, None] <= hor + 3)
        img = comp(img, rgb(P['dark'])[None, None, :] * 0.8, m)
    acc = np.zeros((H, W, 3), np.float32)
    acc = stars(acc, rng, 260, int(hor * 0.45), 0.5)
    return img, acc

def k_olive(rng, P):
    base = sky([(0, rgb(P['top'])), (0.5, rgb(P['mid'])), (0.8, rgb(P['hor'])), (1, rgb(P['hor']) * 0.7)])
    hor = int(H * 0.7)
    img = hills(base, rng, 3, hor - 50, None, rgb(P['haze']), rgb(P['dark']) * 1.3, amp=55)
    ridge = hor + 60 - 45 * (noise1d(W, rng, 4, 0.5, 1) - 0.4)
    img = comp(img, rgb(P['dark'])[None, None, :] * 0.7, mask_below(ridge, 2))
    # lone olive tree
    tx = int(rng.uniform(0.3, 0.7) * W); tb = int(ridge[tx]) + 8
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    th = int(rng.uniform(300, 380))
    d.polygon([(tx - 20, tb), (tx + 20, tb), (tx + 12, tb - th * 0.45), (tx - 10, tb - th * 0.45)], fill=255)
    d.polygon([(tx - 6, tb - th * 0.35), (tx - 120, tb - th * 0.62), (tx - 108, tb - th * 0.66), (tx, tb - th * 0.5)], fill=255)
    d.polygon([(tx + 4, tb - th * 0.38), (tx + 125, tb - th * 0.66), (tx + 112, tb - th * 0.7), (tx - 2, tb - th * 0.5)], fill=255)
    for _ in range(24):
        cx = tx + rng.normal(0, 95); cy = tb - th * rng.uniform(0.6, 0.98)
        rx, ry = rng.uniform(55, 100), rng.uniform(26, 44)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    m = ndi.gaussian_filter(np.asarray(im, np.float32) / 255.0, 1.0)
    img = comp(img, rgb(P['dark'])[None, None, :] * 0.35, m)
    acc = np.zeros((H, W, 3), np.float32)
    acc = stars(acc, rng, 420, int(H * 0.45), 0.7)
    acc = moon(acc, rng.uniform(0.12, 0.88) * W, rng.uniform(0.12, 0.3) * H, 28, 0.2, crescent=True)
    return img, acc

def k_bokeh(rng, P):
    base = vgrad([(0, rgb(P['top'])), (1, rgb(P['hor']))])
    n = noise2d(H, W, 380, rng, 3)
    base = base * (0.75 + 0.5 * n[..., None])
    layer = np.zeros((H, W, 3), np.float32)
    cols = [rgb(c) for c in P['lights']]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    for _ in range(int(rng.integers(26, 46))):
        cx, cy = rng.uniform(0, W), rng.uniform(H * 0.2, H * 1.0)
        r = rng.uniform(26, 120)
        c = cols[rng.integers(len(cols))] * rng.uniform(0.25, 0.75)
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        disc = np.clip((r - d) / 2.5 + 0.5, 0, 1) * (0.55 + 0.45 * (d / r) ** 2)
        layer += disc[..., None] * c[None, None, :]
    layer = ndi.gaussian_filter(layer, (7, 7, 0)) * 0.38
    return base, layer

def k_pasture(rng, P):
    base = sky([(0, rgb(P['top'])), (0.45, rgb(P['mid'])), (0.62, rgb(P['hor'])), (1, rgb(P['hor']) * 0.7)])
    hor = int(H * 0.56)
    img = hills(base, rng, 5, hor, None, rgb(P['haze']), rgb(P['dark']), amp=60, rough=0.5)
    # grass texture on the near field
    g = ndi.gaussian_filter(rng.normal(0, 1, (H, W)).astype(np.float32), (0.6, 6))
    nearm = (np.arange(H)[:, None] > H * 0.7).astype(np.float32) * np.clip((np.arange(H)[:, None] - H * 0.7) / (H * 0.3), 0, 1)
    img = img * (1 + 0.45 * g[..., None] * nearm[..., None])
    img = mist(img, rng, hor, hor + 120, rgb(P['hor']), 0.4, 300)
    acc = np.zeros((H, W, 3), np.float32)
    acc = stars(acc, rng, 380, hor, 0.65)
    acc = moon(acc, rng.uniform(0.15, 0.85) * W, rng.uniform(0.12, 0.3) * H, 26, 0.18, crescent=P.get('crescent', False))
    return img, acc

KINDS = {
 'night_hills': k_night_hills, 'dawn': k_dawn, 'water_moon': k_water_moon, 'mist_mountains': k_mist_mountains,
 'cedars': k_cedars, 'dunes': k_dunes, 'milkyway': k_milkyway, 'clouds': k_clouds, 'sea': k_sea,
 'olive': k_olive, 'bokeh': k_bokeh, 'pasture': k_pasture,
}

# palettes: (name) -> dict
PAL = {
 'navy':    dict(top='#02050f', mid='#06122a', hor='#12304f', haze='#1b3a5c', dark='#050b16', water='#3c6a90', moon=True),
 'teal':    dict(top='#020b10', mid='#07252b', hor='#18484d', haze='#235a5c', dark='#04100f', water='#3d8083', moon=True),
 'violet':  dict(top='#07041a', mid='#1a1040', hor='#4a2d66', haze='#4e3a72', dark='#0b0716', water='#6a5690', moon=True),
 'indigo':  dict(top='#040616', mid='#101a45', hor='#2b3f7a', haze='#34508a', dark='#070b1f', water='#4f6aa8', moon=True),
 'forest':  dict(top='#030a08', mid='#0b2218', hor='#21493a', haze='#2c5846', dark='#050f0b', water='#3f7a62', moon=True),
 'plum':    dict(top='#0d0414', mid='#2c0f3a', hor='#6a3052', haze='#7a4668', dark='#12060f', water='#8a5078', moon=True),
 'amber':   dict(top='#0c0710', mid='#3a1830', hor='#a8552b', haze='#7a4a3a', dark='#140a0c', glow='#ffb070', lit='#ffb878', water='#a86a45', cloud='#e09060', sea1='#5a3a3a', sea2='#1e1618'),
 'rose':    dict(top='#0b0818', mid='#35183c', hor='#c46a5a', haze='#8a5568', dark='#150a12', glow='#ffa890', lit='#ffb4a0', water='#a8606a', cloud='#e8907c', sea1='#58343e', sea2='#1c1218'),
 'gold':    dict(top='#0a0a14', mid='#2a2036', hor='#c28a45', haze='#80623e', dark='#130e0b', glow='#ffd08a', lit='#ffd9a0', water='#a88050', cloud='#f0b878', sea1='#5a4632', sea2='#1c1610'),
 'dawnblue':dict(top='#050a1e', mid='#1b3058', hor='#d89a78', haze='#6a7a9a', dark='#0c1220', glow='#ffc8a0', lit='#ffcfae', water='#8090b0', cloud='#e8b098', sea1='#4a5470', sea2='#141a28'),
 'steel':   dict(top='#04070e', mid='#0f1a2a', hor='#3a4e68', haze='#4a5c78', dark='#080d16', water='#5a6e8a', moon=True),
 'mwblue':  dict(top='#010208', hor='#0a1230', mw='#7a8fc8', dark='#030509', trees=True),
 'mwviolet':dict(top='#03010a', hor='#160c30', mw='#b09ad8', dark='#050309', trees=True),
 'mwteal':  dict(top='#010609', hor='#0a2430', mw='#7ac4c8', dark='#020708', trees=False),
 'warm':    dict(top='#0c0603', hor='#1e0f08', lights=['#ffb45a', '#ff9a3c', '#ffd28a', '#ffc070'], ),
 'cool':    dict(top='#030914', hor='#0a1a2c', lights=['#7ab0ff', '#9ac8ff', '#c8e0ff', '#6a98e8']),
 'gold2':   dict(top='#0a0704', hor='#1a1008', lights=['#ffd070', '#ffb84a', '#ffe0a0', '#ffa840']),
}

# 66 scene plan: (kind, palette, extras)
PLAN = []
def add(kind, pal, **kw): PLAN.append((kind, pal, kw))
for p, mo in [('navy', 1), ('teal', 1), ('violet', 0), ('indigo', 1), ('forest', 0), ('plum', 1)]:
    add('night_hills', p, moon=bool(mo), crescent=(p in ('teal', 'plum')))
for p in ['amber', 'rose', 'gold', 'dawnblue', 'rose', 'amber']:
    add('dawn', p)
for p, cr in [('navy', 0), ('indigo', 1), ('teal', 0), ('violet', 1), ('steel', 0), ('forest', 1)]:
    add('water_moon', p, crescent=bool(cr))
for p, mo in [('steel', 1), ('navy', 0), ('violet', 1), ('teal', 0), ('indigo', 1), ('plum', 0)]:
    add('mist_mountains', p, moon=bool(mo))
for p, mo in [('amber', 1), ('rose', 1), ('indigo', 1), ('dawnblue', 0), ('violet', 1), ('forest', 1)]:
    add('cedars', p, moon=bool(mo))
for p in ['amber', 'rose', 'gold', 'dawnblue', 'violet', 'plum']:
    add('dunes', p)
for p in ['mwblue', 'mwviolet', 'mwteal', 'mwblue', 'mwviolet']:
    add('milkyway', p)
for p in ['amber', 'rose', 'gold', 'dawnblue', 'violet', 'plum']:
    add('clouds', p)
for p, hl in [('amber', 1), ('rose', 0), ('gold', 1), ('dawnblue', 0), ('violet', 1)]:
    add('sea', p, headland=bool(hl))
for p in ['amber', 'rose', 'gold', 'dawnblue', 'violet']:
    add('olive', p)
for p in ['warm', 'cool', 'gold2', 'warm', 'cool']:
    add('bokeh', p)
for p, cr in [('navy', 1), ('forest', 0), ('indigo', 0), ('teal', 1)]:
    add('pasture', p, crescent=bool(cr))
assert len(PLAN) == 66, len(PLAN)

def render(i, outdir):
    kind, pal, kw = PLAN[i]
    P = dict(PAL[pal]); P.update(kw)
    # fill missing keys for kinds that use them
    for k, v in dict(top='#03050c', mid='#0b1426', hor='#1c3050', haze='#2a4468', dark='#060a12', glow='#ffc080', lit='#ffc080', water='#4a6a90', cloud='#c08a70', sea1='#3a4a60', sea2='#10161f').items():
        P.setdefault(k, v)
    rng = np.random.default_rng(1000 + i * 7919)
    img, acc = KINDS[kind](rng, P)
    target = {'bokeh': 17, 'milkyway': 15, 'dawn': 30, 'sea': 28, 'clouds': 29, 'dunes': 28}.get(kind, 24) + rng.uniform(-2, 3)
    im = finish(img, rng, target, acc)
    path = f'{outdir}/scene_{i:02d}.png'
    im.save(path, optimize=False, compress_level=3)
    return path, kind, pal, float(np.asarray(im).astype(np.float32).dot([0.2126, 0.7152, 0.0722]).mean())

if __name__ == '__main__':
    outdir = sys.argv[1]
    idx = [int(x) for x in sys.argv[2:]] or range(len(PLAN))
    for i in idx:
        p, k, pal, m = render(i, outdir)
        print(f'{i:02d} {k:15s} {pal:9s} mean_luma={m:5.1f}', flush=True)
