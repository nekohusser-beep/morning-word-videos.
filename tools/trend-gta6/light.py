import sys
from common import *

LS = 30.40; END = 59.0
tG = START['eph'] - 0.15; tH = START['house'] - 0.16; tI = START['prayer'] - 0.15; tJ = START['ask'] - 0.12
XF = 0.25
SRC = [('bg/psalm.mp4', LS, tG + XF, 0.0), ('bg/eph.mp4', tG - XF, tH + XF, 0.0), ('bg/home.mp4', tH - XF, tI + XF, 0.6), ('bg/eagle.mp4', tI - XF, END + 1, 0.0)]
VIGL = (vignette(0.50, 2.0, band=(900, 400, 0.40)).astype(np.float32) * 0.86).astype(np.uint8)
CX = W / 2


def serif(lines, size, cy, times, t_out, italic=False, fill=WHITE, maxw=900, lhf=1.30, fo=0.28):
    f, s = fit(lines, LORAI if italic else LORA, size, maxw, 600)
    return Block(layout(lines, f, CX, cy, fill=fill, shadow=16, sh_alpha=220, lh=int(s * lhf), key=('L', italic, s)), times, t_out, style='soft', fo=fo)


def mont(text, size, cy, t0, t_out, fill=GOLD, track=8, wght=800, fo=0.25):
    f = font(MONT, size, wght)
    return Block(layout([[text]], f, CX, cy, fill=fill, shadow=12, track=track, sh_alpha=220, key=('M', size, wght)), [t0], t_out, style='soft', fo=fo)


def anton(lines, size, cy, times, t_out, maxw=900, fo=0.14):
    f, s = fit(lines, ANTON, size, maxw)
    return Block(layout(lines, f, CX, cy, stroke=7, shadow=16, lh=int(s * 1.13), key=('A', s)), times, t_out, fo=fo)


B = []
# F: Psalm 101:3
o = tG - 0.20
B.append(serif([['David', 'said,']], 58, 560, [wt('psalm', 0), wt('psalm', 1)], o, italic=True, fill=GOLD))
B.append(serif([['I', 'will', 'set'], ['no', 'wicked', 'thing'], ['before', 'mine', 'eyes']], 106, 850, [wt('psalm', i) for i in range(2, 11)], o))
B.append(mont('PSALM 101:3', 52, 1150, wt('psalm', 11), o))
B.append(mont('KING JAMES VERSION', 25, 1215, wt('psalm', 11) + 0.3, o, fill=GREY, track=6, wght=600))
# G: Ephesians 5:11
o = tH - 0.30
B.append(serif([['Paul', 'wrote,']], 58, 500, [wt('eph', 0), wt('eph', 1)], o, italic=True, fill=GOLD))
B.append(serif([['And', 'have', 'no', 'fellowship'], ['with', 'the', 'unfruitful'], ['works', 'of', 'darkness,'], ['but', 'rather', 'reprove', 'them.']], 88, 840,
               [wt('eph', i) for i in range(2, 16)], o))
B.append(mont('EPHESIANS 5:11', 52, 1190, wt('eph', 16), o))
B.append(mont('KING JAMES VERSION', 25, 1255, wt('eph', 16) + 0.3, o, fill=GREY, track=6, wght=600))
# H: your house
B.append(anton([['OWN', 'THE', 'CONSOLE'], ['IF', 'YOU', 'WANT.']], 170, 880, [wt('house', i) for i in range(6)], wt('house', 6) - 0.06, fo=0.05))
B.append(anton([['JUST', 'KNOW'], ["WHAT'S", 'PLAYING'], ['IN', ('YOUR', GOLD), ('HOUSE.', GOLD)]], 190, 880, [wt('house', i) for i in range(6, 13)], tI - 0.22, fo=0.2))
# I: prayer
o = tJ - 0.18
B.append(serif([['Father,'], ['guard', 'our', 'eyes'], ['and', 'guard', 'our', 'homes,'], ['in', "Jesus'", 'name.']], 92, 930, [wt('prayer', i) for i in range(11)], o, italic=True, fo=0.18))
B.append(serif([['Amen.']], 120, 1290, [wt('prayer', 11)], o, italic=True, fill=GOLD, fo=0.18))
# J: ask
B.append(anton([['TYPE']], 150, 790, [wt('ask', 0)], END + 1))
f_am, s_am = fit([['AMEN']], ANTON, 340, 880)
AMEN = Block(layout([[('AMEN', GOLD)]], f_am, CX, 1040, stroke=8, shadow=18, lh=int(s_am * 1.13), key='amen'), [wt('ask', 1)], END + 1)
B.append(AMEN)
fj = font(MONT, 52, 700)
B.append(Block(layout([['and', 'send', 'this', 'to', 'a', 'friend'], ['who', 'needs', 'it.']], fj, CX, 1315, shadow=14, sh_alpha=230, lh=74, key='mj'), [wt('ask', i) for i in range(2, 11)], END + 1, style='soft'))


class Light:
    def __init__(self, t_from=LS):
        self.r = {}; self.t_from = t_from

    def bg(self, t):
        acc = None
        for path, a, b, ss in SRC:
            if a <= t < b:
                if path not in self.r: self.r[path] = Vid(path, ss + max(0.0, t - a))
                f = self.r[path].read()
                w = min(1.0, (t - a) / (2 * XF)) if a > LS else 1.0
                acc = f if acc is None else cv2.addWeighted(acc, 1 - w, f, w, 0)
            elif t >= b and path in self.r:
                self.r.pop(path).close()
        return acc.copy()

    def frame(self, t, i):
        fr = mul(self.bg(t), VIGL)
        fr = grain(fr, i, 2.5)
        for b in B: b.draw(fr, t)
        brand(fr, 0.72)
        if t < LS + 0.45: fr = cv2.convertScaleAbs(fr, alpha=eio((t - LS) / 0.45))
        return fr


if __name__ == '__main__':
    if sys.argv[1] == 'prev':
        for s in sys.argv[2:]:
            t = float(s); fr = Light(t).frame(t, int(t * FPS)); Image.fromarray(fr).save(f'prev/l_{t:05.2f}.jpg', quality=88)
    else:
        L = Light(); i0 = int(round(LS * FPS)); n = int(round(END * FPS)) - i0; wr = writer('light.tmp.mp4')
        for k in range(n):
            i = i0 + k; wr.stdin.write(L.frame(i / FPS, i).tobytes())
        wr.stdin.close(); wr.wait(); os.rename('light.tmp.mp4', 'light.mp4'); print('light frames', n)
