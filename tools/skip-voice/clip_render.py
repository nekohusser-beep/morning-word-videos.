#!/usr/bin/env python3
"""Big Skip clip renderer: animated i2v clips + locked voice lines -> 1080x1920 Short.

python3 clip_render.py cfg.json out.mp4

cfg = {
  "voices": "dir with u###.wav (idx = line index in lines.json)",
  "lines": "lines.json",
  "gap": 0.12,                       # silence between lines
  "shots": [{"clip": "c1.mp4", "lines": [0], "tail": 0.0}, ...],   # each shot covers its lines
  "hook": ["DRE CAMPED OUT", "FOR BLACK FRIDAY", "SINCE THANKSGIVING"],  # top-center, 1.2 s each from frame 1
  "end": ["TAG THE FRIEND WHO'D", "STILL CAMP OUT"], "end_hold": 1.6
}
First word lands on frame 1. Captions (2-3 words) run under every spoken line. Output -14 LUFS.
"""
import json, os, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SR = 1080, 1920, 24, 48000
FONT = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'


def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).decode().strip())


def load_wav(p):
    a, sr = sf.read(p, dtype='float32', always_2d=True)
    a = a.mean(1)
    if sr != SR:
        x = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))
        a = np.interp(x, np.arange(len(a)), a).astype('float32')
    # trim edge silence
    nz = np.where(np.abs(a) > 0.01)[0]
    if len(nz):
        a = a[max(0, nz[0] - int(0.02 * SR)): nz[-1] + int(0.06 * SR)]
    return a


def card(texts, size, y, path, box=True, color=(255, 255, 255), stroke=(0, 0, 0)):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, size)
    lines = texts if isinstance(texts, list) else [texts]
    hs = [d.textbbox((0, 0), t, font=f, stroke_width=8) for t in lines]
    tot = sum(b[3] - b[1] for b in hs) + 14 * (len(lines) - 1)
    cy = y
    if box:
        wmax = max(b[2] - b[0] for b in hs)
        d.rounded_rectangle([W / 2 - wmax / 2 - 34, cy - 22, W / 2 + wmax / 2 + 34, cy + tot + 30], 28, fill=(255, 214, 0, 235))
        color, stroke = (20, 16, 24), (255, 255, 255)
    for t, b in zip(lines, hs):
        w = b[2] - b[0]
        d.text((W / 2 - w / 2 - b[0], cy - b[1]), t, font=f, fill=color, stroke_width=0 if box else 8, stroke_fill=stroke)
        cy += (b[3] - b[1]) + 14
    im.save(path)


def chunks(text, n=3):
    w = text.replace('—', ' ').split()
    out, cur = [], []
    for x in w:
        cur.append(x)
        if len(cur) >= n or x.endswith(('.', '?', '!', ',')):
            out.append(' '.join(cur)); cur = []
    if cur: out.append(' '.join(cur))
    return out


def main(cfgp, outp):
    cfg = json.load(open(cfgp)); base = os.path.dirname(os.path.abspath(cfgp))
    P = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    lines = json.load(open(P(cfg['lines'])))
    gap = cfg.get('gap', 0.12)
    wavs = {i: load_wav(os.path.join(P(cfg['voices']), f'u{i:03d}.wav')) for i in range(len(lines))}
    # line timeline
    t = 0.0; starts = {}
    order = [i for s in cfg['shots'] for i in s['lines']]
    shot_spans = []
    for s in cfg['shots']:
        s0 = t
        for i in s['lines']:
            starts[i] = t; t += len(wavs[i]) / SR + gap
        t += s.get('tail', 0.0)
        shot_spans.append((s0, t))
    end_hold = cfg.get('end_hold', 1.6)
    total = t + end_hold
    shot_spans[-1] = (shot_spans[-1][0], total)
    # audio
    mix = np.zeros(int(total * SR) + SR, 'float32')
    for i in order:
        a = wavs[i]; k = int(starts[i] * SR); mix[k:k + len(a)] += a
    tmp = tempfile.mkdtemp()
    sf.write(f'{tmp}/vo.wav', mix[:int(total * SR)], SR)
    # video shots: fit each clip to its span (slow to 1.35x max, then hold last frame)
    parts = []
    for j, (s, (a, b)) in enumerate(zip(cfg['shots'], shot_spans)):
        need = b - a; cd = dur(P(s['clip'])) - 0.05
        k = min(1.35, max(1.0, need / cd))
        pad = max(0.0, need - cd * k)
        vf = (f"setpts={k:.4f}*PTS,scale={W}:-2:flags=lanczos,crop={W}:min(ih\\,{H}),pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,"
              f"tpad=stop_mode=clone:stop_duration={pad + 0.2:.3f},trim=duration={need:.4f},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p")
        o = f'{tmp}/p{j}.mp4'
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', P(s['clip']), '-an', '-vf', vf, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', o], check=True)
        parts.append(o)
    open(f'{tmp}/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', f'{tmp}/list.txt', '-c', 'copy', f'{tmp}/base.mp4'], check=True)
    # overlays
    ov = []
    hk = cfg.get('hook', [])
    for n, h in enumerate(hk):
        p = f'{tmp}/h{n}.png'; card(h if isinstance(h, list) else [h], 74, 150, p)
        ov.append((p, n * 1.2, (n + 1) * 1.2 if n < len(hk) - 1 else max(3.6, (n + 1) * 1.2)))
    for i in order:
        cs = chunks(lines[i]['text']); L = len(wavs[i]) / SR
        for n, c in enumerate(cs):
            p = f'{tmp}/c{i}_{n}.png'; card([c.upper()], 82, 1380, p, box=False)
            ov.append((p, starts[i] + L * n / len(cs), starts[i] + L * (n + 1) / len(cs)))
    if cfg.get('end'):
        p = f'{tmp}/end.png'; card(cfg['end'], 70, 150, p)
        ov.append((p, total - end_hold, total + 1))
    args = ['ffmpeg', '-y', '-v', 'error', '-i', f'{tmp}/base.mp4', '-i', f'{tmp}/vo.wav']
    for p, _, _ in ov: args += ['-i', p]
    fc, last = [], '0:v'
    for n, (p, a, b) in enumerate(ov):
        o = f'v{n}'; fc.append(f"[{last}][{n + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[{o}]"); last = o
    fc.append('[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]')
    args += ['-filter_complex', ';'.join(fc), '-map', f'[{last}]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
             '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-t', f'{total:.3f}', '-movflags', '+faststart', outp]
    subprocess.run(args, check=True)
    print(f'{outp}: {total:.1f} s, {len(ov)} overlays; line starts', {k: round(v, 2) for k, v in starts.items()})


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
