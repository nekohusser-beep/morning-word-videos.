import sys
from common import *
from common import _draw

# ============ timeline ============
tA_END = START['s2'] - 0.12                      # act I (red) ends
tTRI = wt('v2', 13)                              # "triumphing"
tX0 = START['s3'] - 0.10                         # crossfade into the dawn clips
SEG = [tX0, tX0 + 7.30, tX0 + 14.60]             # clip starts (each clip 7.87 s)
XF = 0.55
WARM = (250, 238, 205)

# ============ procedural fire / light background (low-res, upscaled) ============
LW, LH = 270, 480
_rng2 = np.random.default_rng(11)


def pnoise(h, w, oh, ow):
    g = _rng2.random((h, w)).astype(np.float32)
    big = np.tile(g, (3, 3))
    r = cv2.resize(big, (ow * 3, oh * 3), interpolation=cv2.INTER_CUBIC)
    return r[oh:2 * oh, ow:2 * ow]


N1 = pnoise(6, 4, 960, 270); N2 = pnoise(14, 8, 960, 270); N3 = pnoise(34, 18, 960, 270)
GY, GX = np.mgrid[0:LH, 0:LW].astype(np.float32)
PROF = (np.clip(GY / LH, 0, 1) ** 1.5 * 0.95 + 0.10).astype(np.float32)
PROF = PROF[..., None] if False else PROF


def lut(g):
    def ramp(pts):
        xs = [p[0] for p in pts]; out = np.zeros((256, 3), np.float32)
        for c in range(3): out[:, c] = np.interp(np.linspace(0, 1, 256), xs, [p[1][c] for p in pts])
        return out
    red = ramp([(0, (0, 0, 0)), (0.22, (34, 3, 2)), (0.48, (150, 22, 6)), (0.74, (238, 84, 14)), (1.0, (255, 176, 64))])
    gold = ramp([(0, (0, 0, 0)), (0.22, (40, 26, 8)), (0.48, (156, 104, 22)), (0.74, (240, 178, 62)), (1.0, (255, 238, 160))])
    return (red * (1 - g) + gold * g).astype(np.uint8)


EMB = np.random.default_rng(5)
EP = [(EMB.random(), EMB.random(), 0.04 + 0.10 * EMB.random(), EMB.random() * 6.28, 0.7 + 1.9 * EMB.random()) for _ in range(150)]


def remap_tex(tex, offy, offx=0.0):
    my = (GY * 2 + offy).astype(np.float32); mx = (GX + offx).astype(np.float32)
    return cv2.remap(tex, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def fire_bg(t, g, br, burst=0.0, beam=0.0):
    n = 0.52 * remap_tex(N1, -t * 22, t * 1.5) + 0.30 * remap_tex(N2, -t * 46, -t * 2.5) + 0.18 * remap_tex(N3, -t * 90, 0)
    heat = np.clip((n * PROF * 1.45 - 0.26) * 2.3, 0, 1)
    heat = np.clip(heat * (0.9 + 0.1 * math.sin(t * 7.3)), 0, 1)
    img = lut(g)[(heat * 255).astype(np.uint8)].astype(np.float32)
    # embers rise
    lay = np.zeros((LH, LW, 3), np.float32)
    ec = np.array([255, 150 + 90 * g, 50 + 130 * g], np.float32)
    for (x0, y0, sp, ph, sz) in EP:
        yy = (y0 - t * sp * (0.6 + 0.8 * g)) % 1.0; xx = (x0 + 0.03 * math.sin(t * 1.3 + ph)) % 1.0
        a = 0.5 + 0.5 * math.sin(t * 3 + ph)
        cv2.circle(lay, (int(xx * LW), int(yy * LH)), max(1, int(sz)), (ec * a).tolist(), -1, cv2.LINE_AA)
    img += cv2.GaussianBlur(lay, (0, 0), 1.2) * 1.15
    if beam > 0:   # light column from above
        cx = LW * 0.5; col = np.exp(-((GX - cx) ** 2) / (2 * (LW * 0.11) ** 2)) * (1 - 0.6 * GY / LH)
        img += col[..., None] * beam * np.array([255, 214, 120], np.float32) * 0.55
    if burst > 0:
        rr = np.sqrt(((GX - LW * 0.5) / (LW * 0.55)) ** 2 + ((GY - LH * 0.46) / (LH * 0.40)) ** 2)
        img += np.exp(-rr * rr * 1.4)[..., None] * burst * np.array([255, 236, 170], np.float32)
    img = np.clip(img * br, 0, 255).astype(np.uint8)
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC)


# ============ text ============
AL_ = 1.13


def anton(lines, size, cx, cy, maxw=900, fill=WHITE, stroke=7, shadow=16, key=None):
    f, s = fit(lines, ANTON, size, maxw)
    return layout(lines, f, cx, cy, fill=fill, stroke=stroke, shadow=shadow, lh=int(s * AL_), key=('A', s)), s


CX = 540
# ---- hook ----
h1, _ = anton([['WHAT', 'DID', 'JESUS']], 150, CX, 600, 900)
h2, _ = anton([['DO', 'IN']], 150, CX, 770, 900)
h3, _ = anton([[('HELL', RED)]], 340, CX, 985, 900)
h4, _ = anton([['FOR', '3', 'DAYS?']], 150, CX, 1235, 900)
HK = Block(h1 + h2 + h3 + h4, [0.0 + 0.02, wt('hook', 1), wt('hook', 2), wt('hook', 3), wt('hook', 4), wt('hook', 5), wt('hook', 6), wt('hook', 7), wt('hook', 8)], wt('hook', 9) - 0.06, fo=0.10)
fm = font(MONT, 52, 800)
k1 = layout([['EVERYONE', 'HAS', 'A', 'STORY'], ['ABOUT', 'IT.']], fm, CX, 880, fill=GREY, shadow=12, track=4, lh=76, key='m52')
HK2 = Block(k1, [wt('hook', i) for i in (9, 10, 11, 12, 13, 14)], wt('hook', 15) - 0.06, style='soft', fo=0.10)
k2 = layout([['HERE', 'IS', 'WHAT', 'THE'], [('BIBLE', GOLD), 'ACTUALLY', 'SAYS.']], fm, CX, 880, fill=WHITE, shadow=12, track=4, lh=76, key='m52')
HK3 = Block(k2, [wt('hook', i) for i in (15, 16, 17, 18, 19, 20, 21)], lend('hook') + 0.10, style='soft', fo=0.12)

# ---- s1 ----
s1a, _ = anton([['HE', 'DID', 'NOT']], 190, CX, 800, 900)
s1b, _ = anton([[('STAY.', GOLD)]], 330, CX, 1050, 900)
S1 = Block(s1a + s1b, [wt('s1', i) for i in range(4)], lend('s1') + 0.30, fo=0.14)

# ---- verses ----
VF = font(LORAI, 64, 500)
LF = font(MONT, 32, 800)
RF, _rs = fit([['COLOSSIANS', '2:15']], ANTON, 210, 900)


def verse(text, cy, line_id, label, maxw=900, nwords=None):
    lines = wrap(text, VF, maxw)
    lh = 88
    toks = [ln.split() for ln in lines]
    L = layout(toks, VF, W / 2, cy, fill=WARM, shadow=16, lh=lh, key='v64', sh_alpha=230)
    n = sum(len(t) for t in toks)
    assert n == len(AL[line_id]['heard']), (line_id, n, len(AL[line_id]['heard']))
    times = [wt(line_id, i) for i in range(n)]
    top = cy - lh * len(lines) / 2.0 - 62
    lab = layout([[label]], LF, W / 2, top, fill=GOLD, shadow=10, track=6, key='lab')
    return L, times, lab, top


V1T = 'For thou wilt not leave my soul in hell; neither wilt thou suffer thine Holy One to see corruption.'
V2T = 'And having spoiled principalities and powers, he made a shew of them openly, triumphing over them in it.'
V3T = 'I am he that liveth, and was dead; and, behold, I am alive for evermore, Amen; and have the keys of hell and of death.'
CYV = 1150
v1L, v1t, v1lab, _ = verse(V1T, CYV, 'v1', 'PSALM 16:10  ·  KJV')
v2L, v2t, v2lab, _ = verse(V2T, CYV, 'v2', 'COLOSSIANS 2:15  ·  KJV')
CYV3 = 1330
v3L, v3t, v3lab, _ = verse(V3T, CYV3, 'v3', 'REVELATION 1:18  ·  KJV')
V1 = Block(v1L, v1t, lend('r1') + 0.34, style='soft', fo=0.14)
V2 = Block(v2L, v2t, lend('r2') + 0.34, style='soft', fo=0.14)
V3 = Block(v3L, v3t, lend('r3') + 0.34, style='soft', fo=0.14)
LAB1 = Block(v1lab, [START['v1']], lend('r1') + 0.34, style='soft', fo=0.14)
LAB2 = Block(v2lab, [START['v2']], lend('r2') + 0.34, style='soft', fo=0.14)
LAB3 = Block(v3lab, [START['v3']], lend('r3') + 0.34, style='soft', fo=0.14)

# ---- reference slams ----
r1a, _ = anton([['PSALM']], 170, CX, 530, 900, fill=GOLD)
r1b, _ = anton([['16:10']], 250, CX, 740, 900)
R1 = Block(r1a + r1b, [START['r1'] + 0.02, wt('r1', 1)], lend('r1') + 0.28, fo=0.12)
r2a, _ = anton([['COLOSSIANS']], 170, CX, 530, 900, fill=GOLD)
r2b, _ = anton([['2:15']], 250, CX, 740, 900)
R2 = Block(r2a + r2b, [START['r2'] + 0.02, wt('r2', 1)], lend('r2') + 0.28, fo=0.12)
r3a, _ = anton([['REVELATION']], 170, CX, 530, 900, fill=GOLD)
r3b, _ = anton([['1:18']], 250, CX, 740, 900)
R3 = Block(r3a + r3b, [START['r3'] + 0.02, wt('r3', 1)], lend('r3') + 0.28, fo=0.12)

# ---- s2 ----
s2z, _ = anton([[('AT', GOLD), ('THE', GOLD), ('CROSS,', GOLD)]], 120, CX, 560, 900)
s2a, _ = anton([['THE', 'ENEMY']], 170, CX, 760, 900)
s2b, _ = anton([[('LOST.', RED)]], 330, CX, 990, 900)
s2c, _ = anton([[('OUT', GOLD), ('IN', GOLD), ('THE', GOLD), ('OPEN.', GOLD)]], 120, CX, 1250, 900)
S2 = Block(s2z + s2a + s2b + s2c, [wt('s2', i) for i in range(10)], lend('s2') + 0.20, fo=0.12)

# ---- s3 ----
s3a, _ = anton([['AND', 'HE', 'CAME']], 170, CX, 700, 900)
s3b, _ = anton([['BACK', 'HOLDING']], 150, CX, 870, 900)
s3c, _ = anton([['THE']], 150, CX, 1010, 900)
s3d, _ = anton([[('KEYS.', GOLD)]], 360, CX, 1230, 900)
S3 = Block(s3a + s3b + s3c + s3d, [wt('s3', 0), wt('s3', 1), wt('s3', 2), wt('s3', 3), wt('s3', 4), wt('s3', 5), wt('s3', 6)], lend('s3') + 0.22, fo=0.12)

# ---- close ----
c1, _ = anton([['THE', 'GRAVE', 'IS', 'NOT']], 150, CX, 640, 900)
c2, _ = anton([['THE', 'END', 'OF']], 150, CX, 810, 900)
c3, _ = anton([['YOUR', 'STORY.']], 230, CX, 1010, 900)
C1 = Block(c1 + c2 + c3, [wt('close', i) for i in (1, 2, 3, 4, 5, 6, 7, 8, 9)], wt('close', 10) - 0.05, fo=0.08)
c4, _ = anton([['BECAUSE', 'HE']], 140, CX, 700, 900)
c5, _ = anton([['HOLDS', 'THE']], 190, CX, 880, 900)
c6, _ = anton([[('KEYS.', GOLD)]], 360, CX, 1130, 900)
C2 = Block(c4 + c5 + c6, [wt('close', i) for i in (10, 11, 12, 13, 14)], wt('close', 15) - 0.05, fo=0.08)
c7, _ = anton([['TYPE', ('AMEN', GOLD)]], 230, CX, 780, 900)
c8, _ = anton([['AND', 'SEND', 'THIS', 'TO', 'A']], 110, CX, 1000, 900)
c9, _ = anton([['FRIEND', 'WHO']], 150, CX, 1150, 900)
c10, _ = anton([['NEEDS', 'IT.']], 150, CX, 1310, 900)
C3 = Block(c7 + c8 + c9 + c10, [wt('close', 15), wt('close', 16), wt('close', 17), wt('close', 18), wt('close', 19), wt('close', 20), wt('close', 21), wt('close', 22), wt('close', 23), wt('close', 24), wt('close', 25)][0:2] + [wt('close', 17), wt('close', 18), wt('close', 19), wt('close', 20), wt('close', 21), wt('close', 22), wt('close', 23), wt('close', 24), wt('close', 25)], TOTAL + 5, fo=0.1)

VIG_A = vignette(0.70, 2.0, band=(950, 400, 0.45))
VIG_C = vignette(0.62, 2.0, band=(1330, 300, 0.42))
VIG_X = vignette(0.64, 2.0, band=(950, 420, 0.40))
VIG_CT = vignette(0.0, 2.0, band=(700, 300, 0.30))


def shake(fr, k, seed):
    r = np.random.default_rng(seed)
    return np.roll(np.roll(fr, int(r.integers(-16, 17) * k), axis=1), int(r.integers(-22, 23) * k), axis=0)


VIDS = {}


def clip_frame(k, adv=True):
    if k not in VIDS: VIDS[k] = Vid(f'clip_{k}.mp4')
    return VIDS[k].read()


def grade(fr, lift=1.0):
    f = fr.astype(np.float32)
    f[..., 0] *= 1.04 * lift; f[..., 1] *= 1.0 * lift; f[..., 2] *= 0.93 * lift
    return np.clip(f, 0, 255).astype(np.uint8)


def smooth(p): return eio(clamp(p))



# ============ v3: public-domain art layers (Dore, John Martin, Bosch follower; all Wikimedia Commons PD) ============
ART = '/tmp/work/v3/'
_IMG = {}
def _load(name):
    if name not in _IMG: _IMG[name] = cv2.cvtColor(cv2.imread(ART + name + '.jpg'), cv2.COLOR_BGR2RGB)
    return _IMG[name]

def duotone(fr, g):
    gray = fr.astype(np.float32).mean(axis=2, keepdims=True) / 255.0
    gray = np.clip((gray - 0.05) * 1.18, 0, 1) ** 0.85
    dark = np.array([14, 3, 2], np.float32); mid = np.array([170, 44, 10], np.float32); lite = np.array([255, 196, 110], np.float32)
    dg = np.array([30, 18, 6], np.float32); mg = np.array([170, 118, 30], np.float32); lg = np.array([255, 232, 160], np.float32)
    dark = dark*(1-g)+dg*g; mid = mid*(1-g)+mg*g; lite = lite*(1-g)+lg*g
    lo = np.clip(gray / 0.55, 0, 1); hi = np.clip((gray - 0.55) / 0.45, 0, 1)
    out = dark + (mid - dark) * lo + (lite - mid) * hi
    return np.clip(out, 0, 255).astype(np.uint8)

def crop_cover(img, cx, cy, z):
    ih, iw = img.shape[:2]
    ch = ih / z; cw = ch * W / H
    if cw > iw: cw = iw; ch = cw * H / W
    x0 = min(max(cx * iw - cw / 2, 0), iw - cw); y0 = min(max(cy * ih - ch / 2, 0), ih - ch)
    M = np.float32([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

XFD = 0.50
# name, t0, t1, (cx0,cy0,z0), (cx1,cy1,z1), mode, brightness
PICS = [
  ('pandemonium',       START['v1'] - 0.25, START['s2'] - 0.05, (0.20, 0.50, 1.10), (0.46, 0.52, 1.10), 'color', 1.0),
  ('vandyck-cross',     START['s2'] - 0.05, tX0 + XF + 0.30,    (0.50, 0.30, 1.00), (0.50, 0.29, 1.22), 'color', 0.90),
]

_BM = (1 - 0.40 * np.exp(-((np.arange(H, dtype=np.float32) - 1150) / 240.0) ** 2))[:, None, None].astype(np.float32)

def pic_layer(p, t):
    name, t0, t1, a, b, mode, br = p
    u = smooth(clamp((t - t0) / (t1 - t0)))
    cx = a[0] + (b[0] - a[0]) * u; cy = a[1] + (b[1] - a[1]) * u; z = a[2] + (b[2] - a[2]) * u
    fr = crop_cover(_load(name), cx, cy, z)
    if mode == 'duo':
        gg = smooth((t - (tTRI - 0.35)) / 1.4)
        fr = duotone(fr, gg)
    else:
        f = fr.astype(np.float32)
        f = (f - 128) * 1.10 + 128
        f[..., 0] *= 1.06; f[..., 1] *= 1.0; f[..., 2] *= 0.86
        fr = np.clip(f, 0, 255).astype(np.uint8)
    return np.clip(fr.astype(np.float32) * br * _BM, 0, 255).astype(np.uint8)

def pics_over(fire, t, burst):
    tot = 0.0; acc = None
    for p in PICS:
        t0, t1 = p[1], p[2]
        a = clamp((t - t0) / XFD) * clamp((t1 + XFD - t) / XFD)
        a = smooth(a)
        if a <= 0: continue
        L = pic_layer(p, t).astype(np.float32) * a
        acc = L if acc is None else acc + L
        tot += a
    if acc is None: return fire
    A = min(1.0, tot)
    glow = 0.30 + 0.55 * min(1.0, burst)
    pic = acc / max(tot, 1e-3)
    out = fire.astype(np.float32) * (1 - A) + np.clip(pic + fire.astype(np.float32) * glow, 0, 255) * A
    return np.clip(out, 0, 255).astype(np.uint8)


def frame_at(t, i):
    pt = 0.5 * (1 + math.sin(t * 2 * math.pi * 1.1))           # slow heartbeat pulse in act I/II
    # ---- background ----
    if t < tX0 + XF:
        # gold shift, beam, burst
        g = smooth((t - (tTRI - 0.35)) / 1.4)
        beam = smooth((t - START['s2']) / 2.5) * 0.9 if t >= START['s2'] else 0.0
        burst = 0.0
        if t >= tTRI: burst = 1.25 * math.exp(-(t - tTRI) / 0.55)
        elif t >= tTRI - 0.25: burst = 0.5 * (t - (tTRI - 0.25)) / 0.25
        if t < START['s1']: br = 0.78 + 0.10 * pt + 0.10 * math.exp(-max(0, t - wt('hook', 5)) * 4) * (t >= wt('hook', 5))
        elif t < START['s2']: br = 0.60 + 0.06 * pt           # quiet after "He did not stay"
        else: br = 0.66 + 0.40 * smooth((t - START['s2']) / (tTRI - START['s2'])) + 0.12 * g
        fb = fire_bg(t, g, br * (1 if t < tX0 else 1), burst, beam)
        fb = pics_over(fb, t, burst)
        # slow push-in
        k = 1.0 + 0.06 * (t / tX0)
        M = np.float32([[k, 0, W / 2 * (1 - k)], [0, k, H / 2 * (1 - k)]])
        fb = cv2.warpAffine(fb, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        fb = mul(fb, VIG_A if t < tX0 else VIG_X)
    if t >= tX0:
        q = clamp((t - tX0) / XF)
        c0 = clip_frame(0)
        fc = grade(c0, 0.94)
        if t >= SEG[1]:
            q1 = clamp((t - SEG[1]) / XF); c1f = grade(clip_frame(1), 0.96)
            fc = cv2.addWeighted(fc, 1 - q1, c1f, q1, 0) if q1 < 1 else c1f
        if t >= SEG[2]:
            q2 = clamp((t - SEG[2]) / XF); c2f = grade(clip_frame(2), 1.0)
            fc = cv2.addWeighted(fc, 1 - q2, c2f, q2, 0) if q2 < 1 else c2f
        fc = mul(mul(fc, VIG_C), VIG_CT)
        fr = cv2.addWeighted(fb, 1 - q, fc, q, 0) if q < 1 else fc
    else:
        fr = fb
    fr = grain(fr, i, 5.0)

    # ---- text ----
    HK.draw(fr, t); HK2.draw(fr, t); HK3.draw(fr, t)
    S1.draw(fr, t); V1.draw(fr, t); LAB1.draw(fr, t); R1.draw(fr, t)
    S2.draw(fr, t); V2.draw(fr, t); LAB2.draw(fr, t); R2.draw(fr, t)
    S3.draw(fr, t); V3.draw(fr, t); LAB3.draw(fr, t); R3.draw(fr, t)
    C1.draw(fr, t); C2.draw(fr, t); C3.draw(fr, t)
    brand(fr, 0.66)

    # ---- hits ----
    for t0, dur, k in [(0.03, 0.20, 0.50), (wt('hook', 5), 0.22, 0.85), (tTRI, 0.12, 0.16)]:
        if t0 <= t < t0 + dur:
            kk = k * (1 - (t - t0) / dur); fr = glitch(fr, kk, i); fr = shake(fr, kk, i + 99)
    if t > TOTAL - 0.45: fr = cv2.convertScaleAbs(fr, alpha=max(0.0, (TOTAL - t) / 0.45))
    return fr


if __name__ == '__main__':
    if sys.argv[1] == 'prev':
        os.makedirs('prev', exist_ok=True)
        for s in sys.argv[2:]:
            t = float(s); fr = frame_at(t, int(t * FPS)); Image.fromarray(fr).save(f'prev/f_{t:05.2f}.jpg', quality=88)
    else:
        n = int(round(TOTAL * FPS)); wr = writer('frames_v3.tmp.mp4')
        for i in range(n):
            wr.stdin.write(frame_at(i / FPS, i).tobytes())
            if i % 300 == 0: print('frame', i, '/', n, flush=True)
        wr.stdin.close(); wr.wait(); os.rename('frames_v3.tmp.mp4', 'frames_v3.mp4'); print('frames', n)
