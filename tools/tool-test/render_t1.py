import json, math, random, subprocess, sys, os, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
L = json.load(open('lines.json'))
BOLD = '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
POP = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
def F(p, s): return ImageFont.truetype(p, s)
CY = (0, 220, 255); WHITE = (255, 255, 255); ORANGE = (255, 150, 40); RED = (255, 60, 60)

def dur(i):
    with wave.open(f'a{i:02d}.wav') as w: return w.getnframes() / w.getframerate()
DUR = [dur(i) for i in range(len(L))]
TOTAL = sum(DUR)

random.seed(7)
FLAKES = [(random.random() * W, random.random() * H, random.uniform(3, 9), random.uniform(80, 220)) for _ in range(140)]

BG = Image.new('RGB', (W, H))
d0 = ImageDraw.Draw(BG)
for y in range(H):
    t = y / H
    d0.line([(0, y), (W, y)], fill=(int(8 + 10 * t), int(14 + 20 * t), int(34 + 40 * t)))

def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3

def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

def ctext(d, y, text, font, fill, maxw=960, gap=12, stroke=0):
    lines = wrap(d, text, font, maxw)
    for ln in lines:
        b = d.textbbox((0, 0), ln, font=font)
        d.text(((W - (b[2] - b[0])) / 2, y), ln, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
        y += (b[3] - b[1]) + gap + 10
    return y

def bigfit(d, text, maxw=960, start=150, minsize=70):
    s = start
    while s > minsize:
        f = F(BOLD, s)
        if len(wrap(d, text, f, maxw)) <= 2 and all(d.textlength(x, font=f) <= maxw for x in wrap(d, text, f, maxw)): return f
        s -= 6
    return F(BOLD, minsize)

def snow(d, t, strength=1.0):
    for x, y, r, sp in FLAKES[:int(140 * strength)]:
        yy = (y + sp * t) % H; xx = (x + 25 * math.sin(t + y)) % W
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(220, 235, 255))

def frame(i, lt, gt):
    l = L[i]; k = l['kind']; D = DUR[i]
    im = BG.copy(); d = ImageDraw.Draw(im)
    a = ease(lt / 0.35)
    # visual per kind (middle band 560..1250)
    if k == 'hook':
        for r in range(3):
            rr = 120 + ((lt * 260 + r * 160) % 480)
            d.ellipse([W/2 - rr, 900 - rr, W/2 + rr, 900 + rr], outline=CY, width=4)
        d.polygon([(470, 810), (470, 990), (630, 900)], fill=WHITE)
    elif k == 'radar':
        cx, cy, R = W/2, 920, 330
        for rr in (110, 220, 330): d.ellipse([cx-rr, cy-rr, cx+rr, cy+rr], outline=(0, 120, 150), width=3)
        ang = lt * 3.2
        for j in range(18):
            aa = ang - j * 0.05
            d.line([cx, cy, cx + R * math.cos(aa), cy + R * math.sin(aa)], fill=(0, int(220 - j * 11), int(255 - j * 12)), width=6)
        for bx, by in [(0.5, -0.4), (-0.6, 0.2), (0.2, 0.7), (-0.2, -0.75)]:
            d.ellipse([cx + bx*R - 14, cy + by*R - 14, cx + bx*R + 14, cy + by*R + 14], fill=CY)
    elif k == 'counter':
        n = int(50000 * ease(lt / max(1.0, D * 0.55)))
        d.text((W/2, 880), f'{n:,}' + ('+' if n >= 50000 else ''), font=F(BOLD, 210), fill=CY, anchor='mm')
        d.text((W/2, 1060), 'SEARCHES', font=F(POP, 70), fill=WHITE, anchor='mm')
        snow(d, gt, 0.4)
    elif k in ('map', 'dates', 'plain'):
        snow(d, gt, 1.0 if k != 'plain' else 0.5)
        if k == 'plain':
            d.rounded_rectangle([240, 700, 840, 1150], 30, fill=(20, 50, 90), outline=CY, width=5)
            for x in range(240, 840, 100): d.line([x, 700, x, 1150], fill=(40, 80, 130), width=2)
            for y in range(700, 1150, 90): d.line([240, y, 840, y], fill=(40, 80, 130), width=2)
            mx = 540 + 120 * math.sin(lt * 1.5); my = 920 + 60 * math.cos(lt * 1.5)
            d.ellipse([mx - 110, my - 110, mx + 110, my + 110], outline=WHITE, width=18)
            d.line([mx + 78, my + 78, mx + 170, my + 170], fill=WHITE, width=26)
        if k == 'map':
            cx, cy, R = W/2, 1120, 380
            cols = [(255, 210, 60), (255, 140, 30), (230, 40, 40)]
            for j in range(3):
                a0 = 180 + j * 60
                d.pieslice([cx-R, cy-R, cx+R, cy+R], a0, a0 + 60, fill=cols[j])
            d.pieslice([cx-R+90, cy-R+90, cx+R-90, cy+R-90], 180, 360, fill=(14, 26, 60))
            for nm, xy in [('SLIGHT', (cx - R + 45, cy + 45)), ('MODERATE', (cx, cy - R - 40)), ('HIGH', (cx + R - 45, cy + 45))]:
                d.text(xy, nm, font=F(POP, 44), fill=WHITE, anchor='mm')
            target = 270; ang = math.radians(180 + (target - 180) * ease(lt / 1.2) + 3 * math.sin(lt * 5))
            d.line([cx, cy, cx + (R - 110) * math.cos(ang), cy + (R - 110) * math.sin(ang)], fill=WHITE, width=14)
            d.ellipse([cx - 28, cy - 28, cx + 28, cy + 28], fill=WHITE)
        if k == 'dates':
            for j, (dn, dd) in enumerate([('FRI', '13'), ('SAT', '14'), ('SUN', '15')]):
                x = 160 + j * 270; s = ease((lt - j * 0.35) / 0.4)
                if s <= 0: continue
                d.rounded_rectangle([x, 760, x + 220, 1060], 26, fill=WHITE)
                d.rounded_rectangle([x, 760, x + 220, 840], 26, fill=RED)
                d.text((x + 110, 800), dn, font=F(POP, 54), fill=WHITE, anchor='mm')
                d.text((x + 110, 955), dd, font=F(BOLD, 130), fill=(20, 20, 30), anchor='mm')
            d.text((W/2, 1130), 'NOVEMBER', font=F(POP, 70), fill=WHITE, anchor='mm')
    elif k == 'wind':
        for j in range(16):
            y = 650 + j * 40; off = (lt * 900 + j * 137) % (W + 600) - 300
            d.line([off, y, off + 260, y], fill=(170, 220, 255), width=6)
        snow(d, gt, 0.3)
    elif k == 'mountain':
        d.polygon([(80, 1250), (420, 700), (760, 1250)], fill=(60, 80, 110))
        d.polygon([(380, 1250), (720, 620), (1040, 1250)], fill=(80, 100, 130))
        d.polygon([(720, 620), (640, 770), (800, 770)], fill=WHITE)
        d.polygon([(420, 700), (350, 815), (490, 815)], fill=WHITE)
        y = 760 + 230 * ease(lt / max(1, D * 0.7))
        for x in range(60, 1020, 50): d.line([x, y, x + 28, y], fill=CY, width=6)
        d.text((990, y - 40), 'snow level', font=F(POP, 40), fill=CY, anchor='rm')
        snow(d, gt, 0.6)
    elif k == 'warm':
        g = Image.new('RGB', (W, H), (0, 0, 0)); gd = ImageDraw.Draw(g)
        gd.ellipse([240, 600, 840, 1200], fill=ORANGE); g = g.filter(ImageFilter.GaussianBlur(120))
        im = Image.blend(im, Image.eval(g, lambda v: v), 0.45); d = ImageDraw.Draw(im)
        d.ellipse([440, 800, 640, 1000], fill=(255, 200, 80))
    elif k == 'search':
        q = 'CPC hazards outlook'; n = int(len(q) * ease(lt / max(1, D * 0.5)))
        d.rounded_rectangle([90, 850, 990, 990], 70, fill=WHITE)
        d.ellipse([140, 890, 190, 940], outline=(90, 90, 100), width=8); d.line([182, 932, 205, 955], fill=(90, 90, 100), width=9)
        caret = '|' if int(gt * 2) % 2 == 0 else ''
        d.text((240, 920), q[:n] + caret, font=F(POP, 62), fill=(20, 20, 30), anchor='lm')
    elif k == 'end':
        p = 1 + 0.06 * math.sin(lt * 6)
        d.text((W/2, 920), '?', font=F(BOLD, int(360 * p)), fill=CY, anchor='mm')
    # header
    d.rounded_rectangle([300, 150, 780, 240], 45, fill=RED)
    d.text((W/2, 195), 'TOOL TEST #1', font=F(POP, 56), fill=WHITE, anchor='mm')
    # text block
    if k == 'counter':
        ctext(d, 1300, l['small'], F(POP, 62), WHITE, stroke=0)
    else:
        f = bigfit(d, l['big'])
        y0 = 360 if k not in ('hook', 'end', 'plain') else 360
        y = 300 + (1 - a) * 40
        tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(tmp)
        y2 = ctext(td, y + 40, l['big'], f, WHITE + (int(255 * a),), stroke=0)
        im.paste(tmp, (0, 0), tmp); d = ImageDraw.Draw(im)
        if l['small']: ctext(d, 1300, l['small'], F(POP, 64), CY)
    # progress bar
    d.rectangle([0, H - 14, int(W * gt / TOTAL), H], fill=CY)
    return im

def render_scene(i, start):
    D = DUR[i]; n = int(round(D * FPS)); tmp = f's{i:02d}.tmp.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(frame(i, f / FPS, start + f / FPS).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0: os.rename(tmp, f's{i:02d}.mp4')
    return n / FPS

if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        st = 0
        for i in range(len(L)):
            frame(i, DUR[i] * 0.7, st + DUR[i] * 0.7).save(f'p{i:02d}.jpg', quality=85); st += DUR[i]
    else:
        st = 0; real = []
        for i in range(len(L)):
            real.append(render_scene(i, st)); st += DUR[i]
        print(real)
