import json, subprocess, wave, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1080, 1920
L = json.load(open('lines.json'))
SER = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
POP = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
OFF = {'a': [2, 20], 'b': [4, 22], 'c': [3, 15]}
used = {'a': 0, 'b': 0, 'c': 0}

def dur(i):
    with wave.open(f'a{i:02d}.wav') as w: return w.getnframes() / w.getframerate()

def wrap(d, text, font, maxw):
    out, cur = [], ''
    for w_ in text.split():
        t = (cur + ' ' + w_).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: out.append(cur); cur = w_
    out.append(cur); return out

def card(i, l):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    big = l['big']; size = 104 if len(big) < 30 else 92
    f = ImageFont.truetype(SER, size)
    lines = wrap(d, big, f, 900); lh = size + 34
    y0 = 760 - len(lines) * lh // 2
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for j, ln in enumerate(lines):
        sd.text((W/2, y0 + j*lh), ln, font=f, fill=(0, 0, 0, 200), anchor='mt')
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    im = Image.alpha_composite(im, sh); d = ImageDraw.Draw(im)
    for j, ln in enumerate(lines):
        d.text((W/2, y0 + j*lh), ln, font=f, fill=(255, 255, 255, 255), anchor='mt')
    y = y0 + len(lines) * lh + 30
    if l['small']:
        fs = ImageFont.truetype(POP, 58)
        for ln in wrap(d, l['small'], fs, 880):
            d.text((W/2, y), ln, font=fs, fill=(255, 214, 120, 255), anchor='mt', stroke_width=3, stroke_fill=(0, 0, 0, 160)); y += 78
    d.text((W/2, 230), 'BLESSED PRAYERS', font=ImageFont.truetype(POP, 40), fill=(255, 255, 255, 190), anchor='mm')
    im.save(f'card{i}.png')

parts = []
for i, l in enumerate(L):
    card(i, l); D = dur(i); c = l['clip']; ss = OFF[c][used[c]]; used[c] += 1
    tmp = f's{i}.tmp.mp4'
    vf = (f"[0:v]scale=1080:1920,setsar=1,fps=30,eq=brightness=-0.10:saturation=1.05,"
          f"zoompan=z='1+0.0006*on':d=1:s=1080x1920:fps=30,format=yuv420p[bg];"
          f"[1:v]format=rgba,fade=in:st=0:d=0.35:alpha=1[t];[bg][t]overlay=0:0,"
          f"fade=in:st=0:d=0.25,fade=out:st={D-0.25:.2f}:d=0.25[v]")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(ss), '-t', f'{D:.3f}', '-i', f'stock/{c}.mp4', '-loop', '1', '-t', f'{D:.3f}', '-i', f'card{i}.png',
                    '-filter_complex', vf, '-map', '[v]', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', '30', tmp], check=True)
    os.rename(tmp, f's{i}.mp4'); parts.append(f's{i}.mp4')
open('v.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
open('a.txt', 'w').write(''.join(f"file 'a{i:02d}.wav'\n" for i in range(len(L))))
