"""Series thumbnail in the style that wins on heaven/hell topics: real person/scene, huge 2-3 word
question (white + yellow, black stroke), red arrow optional, big red PART badge + series strip."""
import json, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
F = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
W, H = 1280, 720
def font(n): return ImageFont.truetype(F, n)
def frame(src, t, out):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', src, '-frames:v', '1',
                    '-vf', 'crop=1653:930:(iw-1653)*0.5+%d:0,scale=1280:720' % 0, out], check=True)
def fit(d, s, maxw, start):
    n = start
    while d.textlength(s, font=font(n)) > maxw and n > 40: n -= 4
    return font(n)
def build(p, out):
    frame(p['src'], p['t'], '/tmp/f.png')
    im = Image.open('/tmp/f.png').convert('RGB')
    if p.get('flip'): im = im.transpose(Image.FLIP_LEFT_RIGHT)
    im = ImageEnhance.Brightness(im).enhance(p.get('bright', 1.0))
    im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.25)).enhance(1.15)
    # tint: hell = red, heaven = gold, on the image side
    tint = Image.new('RGB', (W, H), tuple(p.get('tint', (190, 40, 10))))
    im = Image.blend(im, tint, p.get('tint_amt', 0.18))
    # dark gradient behind the text (left)
    g = Image.new('L', (W, H)); gp = g.load()
    for x in range(W):
        v = int(235 * max(0, 1 - x / 760) ** 1.2)
        for y in range(H): gp[x, y] = v
    im = Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), im, g).convert('RGBA')
    d = ImageDraw.Draw(im)
    l1, l2 = p['l1'], p['l2']
    f1 = fit(d, l1, 700, 170); f2 = fit(d, l2, 700, 150)
    y = p.get('y', 200)
    for s, f, c, yy in [(l1, f1, (255, 255, 255), y), (l2, f2, (255, 214, 0), y + f1.size + 18)]:
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((50 + 6, yy + 8), s, font=f, fill=(0, 0, 0, 230), stroke_width=14, stroke_fill=(0, 0, 0, 230))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
        d.text((50, yy), s, font=f, fill=c, stroke_width=11, stroke_fill=(0, 0, 0))
    # PART badge + series strip
    d.rounded_rectangle((40, 34, 300, 124), 16, fill=(215, 20, 20), outline=(0, 0, 0), width=5)
    d.text((170, 79), f"PART {p['part']}", font=font(58), fill=(255, 255, 255), anchor='mm')
    d.text((320, 79), p['series'].upper(), font=font(40), fill=(255, 255, 255), anchor='lm', stroke_width=7, stroke_fill=(0, 0, 0))
    if p.get('arrow'):
        x0, y0, x1, y1 = p['arrow']
        mx, my = (x0 + x1) / 2 + 30, (y0 + y1) / 2 - 40
        pts = [(x0, y0), (mx, my), (x1, y1)]
        d.line(pts, fill=(0, 0, 0), width=34, joint='curve'); d.line(pts, fill=(235, 20, 20), width=22, joint='curve')
        a = math.atan2(y1 - my, x1 - mx)
        hd = [(x1 + 44 * math.cos(a), y1 + 44 * math.sin(a)), (x1 + 44 * math.cos(a + 2.3), y1 + 44 * math.sin(a + 2.3)), (x1 + 44 * math.cos(a - 2.3), y1 + 44 * math.sin(a - 2.3))]
        d.polygon(hd, fill=(235, 20, 20), outline=(0, 0, 0), width=6)
    im.convert('RGB').save(out, quality=92)
if __name__ == '__main__':
    for p in json.load(open(sys.argv[1])): build(p, p['out']); print(p['out'])
