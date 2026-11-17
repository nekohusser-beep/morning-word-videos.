import sys, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1280, 720
ANTON = '/home/claude/fonts/Anton.ttf'; POP = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'

def scene(seed=4):
    random.seed(seed)
    im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H; d.line([(0, y), (W, y)], fill=(int(8 + 30 * t), int(18 + 40 * t), int(48 + 70 * t)))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    mx, my = 1080, 130
    for r in range(340, 0, -6): g.ellipse([mx - r, my - r, mx + r, my + r], fill=(170, 200, 255, int(70 * (1 - r / 340) ** 2.2)))
    im = Image.alpha_composite(im.convert('RGBA'), glow); d = ImageDraw.Draw(im)
    d.ellipse([mx - 78, my - 78, mx + 78, my + 78], fill=(250, 246, 225))
    for cx, cy, r in ((mx - 25, my - 20, 14), (mx + 22, my + 25, 10), (mx + 30, my - 30, 8)): d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(228, 224, 205))
    for _ in range(260):
        x, y = random.random() * W, random.random() * H * .6; r = random.choice([1, 1, 1.5, 2]); d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, random.randint(80, 230)))
    # soft clouds
    cl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); c = ImageDraw.Draw(cl)
    for cx, cy, s in ((900, 300, 1.4), (300, 380, 1.8), (1150, 420, 1.2)):
        for dx, dy, r in ((-90, 10, 70), (-20, -20, 95), (70, 5, 75), (140, 25, 55)): c.ellipse([cx + dx * s - r * s, cy + dy * s - r * s, cx + dx * s + r * s, cy + dy * s + r * s], fill=(120, 140, 200, 70))
    cl = cl.filter(ImageFilter.GaussianBlur(30)); im = Image.alpha_composite(im, cl); d = ImageDraw.Draw(im)
    # glowing open Bible on a blanket
    fg = Image.new('RGBA', (W, H), (0, 0, 0, 0)); b = ImageDraw.Draw(fg)
    b.polygon([(-20, 610), (400, 560), (900, 585), (1300, 560), (1300, 720), (-20, 720)], fill=(60, 82, 140, 255))
    for k in range(7): b.arc([-100 + k * 220, 590 + (k % 2) * 18, 160 + k * 220, 780], 200, 330, fill=(78, 102, 165, 255), width=7)
    gl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gg = ImageDraw.Draw(gl)
    bx, by = 1000, 560
    for r in range(260, 0, -6): gg.ellipse([bx - r * 1.5, by - r, bx + r * 1.5, by + r], fill=(255, 200, 110, int(90 * (1 - r / 260) ** 2)))
    for k in range(9):
        a = math.pi * (1.1 + k * 0.1); gg.polygon([(bx, by - 20), (bx + math.cos(a - .03) * 420, by - 20 + math.sin(a - .03) * 420), (bx + math.cos(a + .03) * 420, by - 20 + math.sin(a + .03) * 420)], fill=(255, 220, 150, 40))
    fg = Image.alpha_composite(fg, gl.filter(ImageFilter.GaussianBlur(8))); b = ImageDraw.Draw(fg)
    b.polygon([(bx - 230, by + 40), (bx, by + 70), (bx + 230, by + 40), (bx + 240, by + 70), (bx, by + 100), (bx - 240, by + 70)], fill=(90, 30, 30, 255))
    b.polygon([(bx - 220, by - 30), (bx - 10, by), (bx - 10, by + 70), (bx - 225, by + 42)], fill=(252, 244, 220, 255))
    b.polygon([(bx + 220, by - 30), (bx + 10, by), (bx + 10, by + 70), (bx + 225, by + 42)], fill=(248, 238, 210, 255))
    for k in range(6):
        yy = by - 12 + k * 11
        b.line([(bx - 195, yy - 18 + k * 1), (bx - 35, yy + 8)], fill=(170, 150, 120, 255), width=3); b.line([(bx + 35, yy + 8), (bx + 195, yy - 18 + k * 1)], fill=(170, 150, 120, 255), width=3)
    b.line([(bx, by), (bx, by + 72)], fill=(150, 120, 90, 255), width=4)
    im = Image.alpha_composite(im, fg)
    # blue moonlight wash + vignette
    vig = Image.new('L', (W, H), 0); ImageDraw.Draw(vig).ellipse([-300, -250, W + 300, H + 300], fill=255); vig = vig.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new('RGBA', (W, H), (0, 0, 10, 190)); im = Image.composite(im, Image.alpha_composite(im, dark), vig)
    return im.convert('RGB')

def fit(d, text, maxw, start):
    s = start
    while s > 40:
        f = ImageFont.truetype(ANTON, s)
        if d.textlength(text, font=f) <= maxw: return f
        s -= 4
    return ImageFont.truetype(ANTON, 40)

def thumb(line1, line2, small, out, seed=4):
    im = scene(seed); d = ImageDraw.Draw(im)
    X = 70; maxw = 780
    f1 = fit(d, line1, maxw, 150); f2 = fit(d, line2, maxw, 150)
    y = 60
    for txt, f in ((line1, f1), (line2, f2)):
        bb = d.textbbox((X, y), txt, font=f)
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((X + 6, y + 8), txt, font=f, fill=(0, 0, 0, 220))
        im = Image.alpha_composite(im.convert('RGBA'), sh.filter(ImageFilter.GaussianBlur(6))).convert('RGB'); d = ImageDraw.Draw(im)
        d.text((X, y), txt, font=f, fill=(255, 255, 255), stroke_width=3, stroke_fill=(10, 10, 20))
        y = bb[3] + 14
        if txt is line1:
            d.rectangle([X, y, X + min(maxw, bb[2] - X + 10), y + 14], fill=(225, 30, 40)); y += 20
        else: y += 10
    if small:
        f = ImageFont.truetype(POP, 40); tw = d.textlength(small, font=f)
        d.rounded_rectangle([X, y + 6, X + tw + 40, y + 70], 14, fill=(225, 30, 40)); d.text((X + 20, y + 38), small, font=f, fill=(255, 255, 255), anchor='lm')
    im.save(out, quality=92)

if __name__ == '__main__':
    thumb(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
