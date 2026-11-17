"""Cold open for a long video: lift the strongest lines (speaker's own audio + burned captions),
add a series badge, then a series card, then the untouched original (stream copy).
usage: python cold_open.py plan.json   (plan: list of {src, out, part, total, series, title, clips:[[s,e],...]})"""
import json, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
F = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
def run(*a): subprocess.run(a, check=True)
def font(n): return ImageFont.truetype(F, n)
def outlined(d, xy, s, f, fill, anchor='mm', sw=8):
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=sw, stroke_fill=(0, 0, 0))
def badge(path, series, part, total):
    im = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    t = f'{series.upper()}  ·  PART {part} OF {total}'
    f = font(40); w = d.textlength(t, font=f)
    d.rounded_rectangle((48, 44, 48 + w + 56, 44 + 76), 14, fill=(200, 20, 20, 235))
    d.text((48 + 28, 44 + 38), t, font=f, fill=(255, 255, 255), anchor='lm')
    im.save(path)
def card(path, series, part, total, title, still):
    bg = Image.open(still).convert('RGB').resize((1920, 1080))
    bg = Image.blend(bg, Image.new('RGB', bg.size, (0, 0, 0)), 0.6)
    d = ImageDraw.Draw(bg)
    outlined(d, (960, 330), series.upper(), font(130), (255, 255, 255))
    outlined(d, (960, 500), f'PART {part} OF {total}', font(96), (255, 214, 0))
    outlined(d, (960, 660), title.upper(), font(84), (255, 255, 255))
    outlined(d, (960, 820), 'NEW EVERY WEDNESDAY · 5 AM EASTERN', font(46), (230, 230, 230), sw=5)
    bg.save(path)
def build(p, work):
    os.makedirs(work, exist_ok=True)
    src = p['src']; parts = []
    badge(f'{work}/badge.png', p['series'], p['part'], p['total'])
    for i, (s, e) in enumerate(p['clips']):
        s = max(0, s - 0.12); dur = (e + 0.28) - s; o = f'{work}/c{i}.mp4'
        run('ffmpeg', '-v', 'error', '-y', '-ss', f'{s:.2f}', '-t', f'{dur:.2f}', '-i', src, '-i', f'{work}/badge.png',
            '-filter_complex', f'[0:v][1:v]overlay=0:0,fps=30,format=yuv420p[v];[0:a]afade=t=in:d=0.06,afade=t=out:st={dur-0.1:.2f}:d=0.1,aresample=48000[a]',
            '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', o)
        parts.append(o)
    # series card: 2.6 s, still from the strongest clip, audio = the source's own opening bed
    run('ffmpeg', '-v', 'error', '-y', '-ss', f"{p['clips'][0][0]+0.5:.2f}", '-i', src, '-frames:v', '1', f'{work}/still.png')
    card(f'{work}/card.png', p['series'], p['part'], p['total'], p['title'], f'{work}/still.png')
    o = f'{work}/card.mp4'
    run('ffmpeg', '-v', 'error', '-y', '-loop', '1', '-t', '2.6', '-i', f'{work}/card.png', '-ss', '0', '-t', '2.6', '-i', src,
        '-filter_complex', "[0:v]fps=30,format=yuv420p,fade=t=in:d=0.25[v];[1:a]volume=0.6,afade=t=out:st=2.3:d=0.3,aresample=48000[a]",
        '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-shortest', o)
    parts.append(o)
    ts = []
    for q in parts + [src]:
        t = f'{work}/{os.path.basename(q)}.ts'
        run('ffmpeg', '-v', 'error', '-y', '-i', q, '-c', 'copy', '-bsf:v', 'h264_mp4toannexb', '-f', 'mpegts', t); ts.append(t)
    run('ffmpeg', '-v', 'error', '-y', '-i', 'concat:' + '|'.join(ts), '-c', 'copy', '-bsf:a', 'aac_adtstoasc', '-movflags', '+faststart', p['out'])
if __name__ == '__main__':
    for p in json.load(open(sys.argv[1])):
        build(p, p['out'] + '.work'); print('built', p['out'])
