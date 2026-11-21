import sys
from common import *
from common import _draw

DE = 30.40                      # dark half ends (seconds)
tB = START['ritual'] - 0.07
tDEM = wt('ritual', 31) - 0.02
tC = lend('ritual') + 0.15
tD = START['money'] - 0.12
tE = wt('money', 18) - 0.12
tCAND = wt('ritual', 12) - 0.30


def hero_prep(a):  # soften the maker's marks on the controller (no brand names on screen)
    out = a.copy()
    for (x0, y0, x1, y1) in [(250, 420, 600, 640), (380, 600, 600, 800)]:
        reg = cv2.GaussianBlur(out[y0:y1, x0:x1], (0, 0), 9)
        m = np.zeros((y1 - y0, x1 - x0), np.float32); m[24:-24, 24:-24] = 1; m = cv2.GaussianBlur(m, (0, 0), 14)[..., None]
        out[y0:y1, x0:x1] = (out[y0:y1, x0:x1] * (1 - m) + reg * m).astype(np.uint8)
    return out


HERO = Still('src/hero.png', soften=0.7, prep=hero_prep)
ROOM = Still('src/room.png', soften=1.6)
CAND = Still('src/candles.png', soften=1.5)
NEON = Still('src/neon.png', soften=2.2)
WIND = Still('src/windows.png', soften=1.5)
VIG = vignette(0.66, 2.0, scan=True)
BLACK = np.zeros((H, W, 3), np.uint8)

AL_ = 1.13  # Anton line height factor


def anton(lines, size, cx, cy, maxw=900, fill=WHITE, stroke=7, shadow=16, key=None):
    f, s = fit(lines, ANTON, size, maxw)
    return layout(lines, f, cx, cy, fill=fill, stroke=stroke, shadow=shadow, lh=int(s * AL_), key=('A', s)), s


CX = 530
# ---------- A: hook ----------
a1, _ = anton([['GTA', '6']], 350, CX, 520, 860)
a2, _ = anton([['HAS', 'A', 'HUMAN']], 158, CX, 790)
a3, _ = anton([[('SACRIFICE', RED)]], 236, CX, 985, 900)
a4, _ = anton([['IN', 'IT.']], 158, CX, 1180)
A1 = Block(a1 + a2 + a3 + a4, [-1, -1] + [wt('hook', i) for i in (2, 3, 4, 5, 6, 7)], wt('hook', 8) - 0.10)
a5, _ = anton([["THAT'S", 'NO'], [('RUMOR.', YEL)]], 214, CX, 540, 880)
A2 = Block(a5, [wt('hook', i) for i in (8, 9, 10)], tB - 0.02, fo=0.01)
fs = font(MONT, 34, 800)
a6 = layout([['THE GAMING SITES ALREADY'], ['PUBLISHED THE HOW-TO']], fs, CX, 846, fill=GREY, shadow=10, track=3, lh=48, key='m34')
A3 = Block(a6, [wt('hook', 11), wt('hook', 11) + 0.12], tB - 0.02, style='soft', fo=0.01)


def card(label, head, cy):
    fl = font(MONT, 27, 800); fh = font(LORA, 41, 600)
    ls = wrap('“' + head + '”', fh, 770); hgt = 62 + 50 * len(ls) + 26

    def dr(d, ox, oy):
        _draw(d, (ox + 38, oy + 24), label, fl, RED + (255,), 0, 4)
        for i, l in enumerate(ls): d.text((ox + 38, oy + 62 + 50 * i), l, font=fh, fill=(255, 255, 255, 255))
    return panel(860, hgt, CX, cy + hgt / 2, dr, bar=RED), hgt


_y = 922; CARDS = []
for (lab, head), tt in zip([('GAME RANT', 'How to Sacrifice Someone to Summon a Demon in GTA 6'),
                            ('GAME8', 'Sacrificial Ritual Easter Egg'),
                            ('YAHOO TECH', 'GTA 6’s creepiest secret: pentagram puzzle')],
                           [wt('hook', 11) + 0.1, wt('hook', 13) + 0.1, wt('hook', 15) + 0.2]):
    c, hg = card(lab, head, _y); CARDS.append((c, tt)); _y += hg + 18

# ---------- B: ritual ----------
ftag = font(MONT, 34, 800)
BTAG = layout([['INSIDE THE GAME']], ftag, CX, 345, fill=WHITE, shadow=10, track=7, key='tag'); TAGW = tw('INSIDE THE GAME', ftag, 7)
fsrc = font(MONT, 28, 600)
BSRC = layout([['Documented by Game Rant, Game8 and Yahoo Tech']], fsrc, CX, 1478, fill=GREY, shadow=8, key='src')
PH = [(0, [["THERE'S", 'A', ('WAREHOUSE', YEL)], ['IN', 'THAT', 'GAME']]),
      (6, [['WITH', 'A', ('PENTAGRAM', RED)], ['ON', 'THE', 'FLOOR']]),
      (12, [['AND', ('CANDLES', YEL)], ['ALL', 'AROUND', 'IT,']]),
      (17, [['AND', 'YOU', 'KNOCK'], ['A', 'MAN', 'OUT,']]),
      (23, [['CARRY', 'HIM', 'IN,']]),
      (26, [['AND', 'LAY', 'HIM'], ['ON', 'IT.']])]
BSZ = min(fit(l, ANTON, 150, 880)[1] for _, l in PH)
BB = []
for n, (i0, lines) in enumerate(PH):
    cnt = sum(len(l) for l in lines)
    ws, _ = anton(lines, BSZ, CX, 1010, 880)
    t_out = (wt('ritual', PH[n + 1][0]) if n + 1 < len(PH) else tDEM) - 0.04
    BB.append(Block(ws, [wt('ritual', i0 + j) for j in range(cnt)], t_out, fo=0.03))
d1, _ = anton([['THEN', 'A']], 170, CX, 640)
d2, _ = anton([[('DEMON', RED)]], 380, CX, 905, 900)
d3, _ = anton([['SHOWS', 'UP.']], 210, CX, 1190)
BD = Block(d1 + d2 + d3, [wt('ritual', i) for i in (31, 32, 33, 34, 35)], tC - 0.01, fo=0.01)

# ---------- C: easter egg ----------
fc = font(LORAI, 84, 600)
c1 = layout([['They', 'call', 'that', 'an']], fc, W / 2, 800, fill=(235, 235, 235), shadow=10, key='li84')
C1 = Block(c1, [wt('egg', i) for i in range(4)], tD - 0.02, style='soft', fo=0.01)
c2, _ = anton([['“EASTER', 'EGG.”']], 230, W / 2, 985, 940, stroke=0)
C2 = Block(c2, [wt('egg', 4), wt('egg', 5)], tD - 0.02, fo=0.01)

# ---------- D: money ----------
fm = font(MONT, 44, 800)
D0 = Block(layout([['IT MADE']], fm, CX, 392, fill=GREY, shadow=10, track=9, key='m44'), [wt('money', 0)], tE, style='soft', fo=0.2)
FBIG = font(ANTON, 350)
dB, _ = anton([[('BILLION', YEL)]], 228, CX, 884, 900)
D2 = Block(dB, [wt('money', 3)], tE, fo=0.2)
fd = font(MONT, 54, 800)
D3 = Block(layout([['IN ITS FIRST DAY']], fd, CX, 1036, fill=WHITE, shadow=12, track=6, key='m54'), [wt('money', 4)], tE, style='soft', fo=0.2)
fq = font(MONT, 26, 600)
D4 = Block(layout([['Source: Rockstar Games, via Reuters, Nov 20, 2026']], fq, CX, 1094, fill=GREY, shadow=8, key='m26'), [wt('money', 3) + 0.4], tE, style='soft', fo=0.2)
dl = [['THE', ('BIGGEST', YEL), ('LAUNCH', YEL)], ['ANY', 'GAME', 'OR', 'MOVIE'], ['HAS', 'EVER', 'HAD.']]
dc, _ = anton(dl, 92, CX, 1302, 880)
D5 = Block(dc, [wt('money', 8 + j) for j in range(10)], tE, fo=0.2)
T379 = wt('money', 2)

# ---------- E: living rooms + rating ----------
e1, _ = anton([["IT'S", 'IN', 'A', 'LOT', 'OF']], 124, CX, 470)
e2, _ = anton([[('LIVING', YEL), ('ROOMS', YEL)]], 214, CX, 650, 900)
e3, _ = anton([['TONIGHT.']], 160, CX, 845)
E1 = Block(e1 + e2 + e3, [wt('money', i) for i in range(18, 26)], DE + 1)


def rating(d, ox, oy):
    fa = font(ANTON, 62); fb = font(MONT, 35, 600); fz = font(MONT, 24, 500)
    d.text((ox + 40, oy + 22), 'RATED M', font=fa, fill=RED + (255,))
    d.text((ox + 40 + fa.getlength('RATED M') + 22, oy + 22), 'MATURE 17+', font=fa, fill=(255, 255, 255, 255))
    d.line((ox + 40, oy + 112, ox + 820, oy + 112), fill=(255, 255, 255, 70), width=2)
    rows = [('Blood and Gore', 'Intense Violence'), ('Mature Humor', 'Nudity'), ('Strong Language', 'Strong Sexual Content'), ('Use of Drugs and Alcohol', None)]
    hot = {'Blood and Gore', 'Nudity', 'Strong Sexual Content', 'Use of Drugs and Alcohol'}
    for r, (a, b) in enumerate(rows):
        y = oy + 132 + r * 54
        d.text((ox + 40, y), a, font=fb, fill=(GOLD if a in hot else WHITE) + (255,))
        if b: d.text((ox + 430, y), b, font=fb, fill=(GOLD if b in hot else WHITE) + (255,))
    d.text((ox + 40, oy + 356), 'Source: ESRB rating summary, Grand Theft Auto VI', font=fz, fill=GREY + (255,))


RATE = panel(860, 404, CX, 1215, rating, bar=RED)
tRATE = tE + 0.30


def shake(fr, k, seed):
    r = np.random.default_rng(seed)
    return np.roll(np.roll(fr, int(r.integers(-16, 17) * k), axis=1), int(r.integers(-22, 23) * k), axis=0)


def frame_at(t, i):
    # ---- background ----
    if t < tB:
        p = t / tB; fl = 0.80 + 0.035 * math.sin(t * 9.1) + 0.025 * math.sin(t * 23.7 + 1)
        fr = HERO.frame(1.02 + 0.15 * p, 0.0, -0.12 + 0.2 * p, fl)
    elif t < tC:
        p = (t - tB) / (tC - tB)
        if t < tCAND + 0.5:
            q = (t - tB) / (tCAND + 0.5 - tB)
            fr = ROOM.frame(1.0 + 0.42 * eio(q), -0.42 * eio(q), -0.02, 0.62)
        if t >= tCAND:
            q = (t - tCAND) / (tC - tCAND)
            fl = 0.88 + 0.07 * math.sin(t * 12.3) + 0.05 * math.sin(t * 31.0 + 2) + 0.03 * math.sin(t * 5.1)
            cf = CAND.frame(1.04 + 0.26 * q, 0.1, 0.18 - 0.1 * q, fl)
            if t < tCAND + 0.5: fr = cv2.addWeighted(fr, 1 - (t - tCAND) / 0.5, cf, (t - tCAND) / 0.5, 0)
            else: fr = cf
        if t >= tDEM:
            u = t - tDEM
            red = np.zeros_like(fr); red[..., 0] = 255
            fr = cv2.convertScaleAbs(fr, alpha=0.55)
            fr = cv2.addWeighted(fr, 1.0, red, 0.20 + 0.35 * math.exp(-u * 5) + 0.05 * math.sin(u * 40), 0)
    elif t < tD:
        fr = BLACK.copy()
    else:
        p = (t - tD) / (DE - tD)
        sh = 0.80 + 0.05 * math.sin(t * 3.3) + 0.03 * math.sin(t * 8.7)
        if t < tE + 0.45: fr = NEON.frame(1.34 - 0.24 * p, -0.2 + 0.5 * p, 0.1, sh)
        if t >= tE:
            q = (t - tE) / (DE - tE)
            wf = WIND.frame(1.04 + 0.12 * q, 0.0, 0.25 - 0.4 * q, 0.62)
            if t < tE + 0.45: fr = cv2.addWeighted(fr, 1 - (t - tE) / 0.45, wf, (t - tE) / 0.45, 0)
            else: fr = wf
    fr = mul(fr, VIG)
    fr = grain(fr, i, 5.0 if not (tC <= t < tD) else 2.5)

    # ---- text ----
    if t < tB:
        A1.draw(fr, t); A2.draw(fr, t); A3.draw(fr, t)
        for c, tt in CARDS:
            if t >= tt:
                p = eo((t - tt) / 0.28); comp(fr, c, p, 70 * (1 - p), 0)
    elif t < tC:
        if t < tDEM:
            o = clamp((t - tB) / 0.3)
            for L in BTAG: comp(fr, L, 0.9 * o)
            dot = dict(a=DOT, cx=CX - TAGW / 2 - 34, cy=343); comp(fr, dot, o * (0.55 + 0.45 * (math.sin(t * 6) > 0)))
            for L in BSRC: comp(fr, L, 0.8 * o)
            for b in BB: b.draw(fr, t)
        else:
            BD.draw(fr, t)
    elif t < tD:
        C1.draw(fr, t); C2.draw(fr, t)
    else:
        if t < tE + 0.2:
            D0.draw(fr, t); D2.draw(fr, t); D3.draw(fr, t); D4.draw(fr, t); D5.draw(fr, t)
            if t >= T379:
                v = 3.79 * eo((t - T379) / 1.25)
                ko = 1.0 if t <= tE else max(0, 1 - (t - tE) / 0.2)
                for L in layout([[f'${v:.2f}']], FBIG, CX, 588, stroke=8, shadow=18, key='big'):
                    comp(fr, L, min(1, (t - T379) / 0.1) * ko)
        if t >= tE:
            E1.draw(fr, t)
            if t >= tRATE:
                p = eo((t - tRATE) / 0.3); comp(fr, RATE, p, 0, 60 * (1 - p))
    brand(fr, 0.62)

    # ---- hits ----
    for t0, dur, k in [(0.07, 0.24, 0.45), (wt('hook', 5), 0.22, 0.8), (wt('hook', 8), 0.12, 0.4), (tB, 0.16, 0.6), (tDEM, 0.45, 1.0),
                       (wt('ritual', 33), 0.3, 1.0), (tD, 0.14, 0.5), (wt('money', 3), 0.16, 0.5), (tE, 0.12, 0.35)]:
        if t0 <= t < t0 + dur:
            kk = k * (1 - (t - t0) / dur)
            fr = glitch(fr, kk, i); fr = shake(fr, kk, i + 99)
    if tDEM <= t < tC and (i % 7 == 0): fr = glitch(fr, 0.35, i)
    if t > DE - 0.30: fr = cv2.convertScaleAbs(fr, alpha=max(0.0, (DE - t) / 0.30))
    return fr


_d = Image.new('RGBA', (40, 40), (0, 0, 0, 0)); ImageDraw.Draw(_d).ellipse((8, 8, 32, 32), fill=RED + (255,)); DOT = np.array(_d)

if __name__ == '__main__':
    if sys.argv[1] == 'prev':
        for s in sys.argv[2:]:
            t = float(s); fr = frame_at(t, int(t * FPS)); Image.fromarray(fr).save(f'prev/d_{t:05.2f}.jpg', quality=88)
    else:
        n = int(round(DE * FPS)); wr = writer('dark.tmp.mp4')
        for i in range(n):
            wr.stdin.write(frame_at(i / FPS, i).tobytes())
        wr.stdin.close(); wr.wait(); os.rename('dark.tmp.mp4', 'dark.mp4'); print('dark frames', n)
