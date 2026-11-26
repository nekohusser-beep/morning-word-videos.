#!/usr/bin/env python3
"""Daily Verse Shorts: BLESSED MORNING (5 AM) and REST IN THE WORD (7:30 PM).
Nature footage (Pexels, free) + KJV verse on screen + Kokoro am_michael voice + branded header.
Usage: python3 build.py ep.json footage_dir out.mp4   (needs kokoro-v1.0.onnx + voices-v1.0.bin in $KOKORO_DIR)
ep.json: {"brand": "BLESSED MORNING", "lines": [{"say":..., "big":..., "small":..., "clip": "m-lake0.mp4", "ss": 2}]}
"""
import json, os, subprocess, sys, numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1080, 1920
ep = json.load(open(sys.argv[1])); FD = sys.argv[2]; OUT = sys.argv[3]
KD = os.environ.get('KOKORO_DIR', '.')
SER = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
for p in ['/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf']:
    if os.path.exists(p): SANS = p
GOLD = (255, 214, 120, 255)
from kokoro_onnx import Kokoro
k = Kokoro(f'{KD}/kokoro-v1.0.onnx', f'{KD}/voices-v1.0.bin')
tmp = '/tmp/dv_' + os.path.basename(OUT).replace('.mp4', ''); os.makedirs(tmp, exist_ok=True)

# VOICE FIXES (Nov 26 2026). Kokoro sounds these KJV words out wrong from their spelling: "goest" came out as
# "ghost" on the Nov 24 card (caught by Gemini, proven with wav2vec2 phones; Whisper's language model hid it).
# Respelling the text makes it worse ("go-est" is read as letters), so the sounds are given directly.
# Scripture on screen is never touched: this only changes what the voice is told to pronounce.
import re
FIX = {
    'goest': 'ɡˈoʊɪst',            # GO-ist, not "ghost"
    'hast': 'hˈæst',               # rhymes with "fast", not "haste"
    'strengtheneth': 'stɹˈɛŋθənəθ',  # STRENGTH-en-eth, not "streng-THEE-neth"
    'zephaniah': 'zˌɛfənˈaɪə',     # zef-uh-NYE-uh
    'commune': 'kəmjˈuːn',         # the verb: kuh-MYOON
}
_FIXRX = re.compile(r"\b(%s)\b" % '|'.join(FIX), re.I)

def speak(text, voice, speed):
    if not _FIXRX.search(text):
        return k.create(text, voice=voice, speed=speed, lang='en-us')
    out = []
    for part in _FIXRX.split(text):
        if part.lower() in FIX:
            out.append(FIX[part.lower()])
        elif part.strip():
            out.append(k.tokenizer.phonemize(part.strip(), 'en-us'))
    ph = re.sub(r"\s+([.,;:?!])", r"\1", ' '.join(out))
    return k.create(ph, voice=voice, speed=speed, lang='en-us', is_phonemes=True)

def wrap(d, text, font, maxw):
    out, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: out.append(cur); cur = w
    out.append(cur); return out

def card(i, l):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    big = l['big']; size = 96 if len(big) < 40 else (84 if len(big) < 90 else 72)
    f = ImageFont.truetype(SER, size); d = ImageDraw.Draw(im)
    lines = wrap(d, big, f, 920); lh = size + 30
    y0 = 860 - len(lines) * lh // 2
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for j, ln in enumerate(lines): sd.text((W/2, y0 + j*lh), ln, font=f, fill=(0, 0, 0, 210), anchor='mt')
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(16))); d = ImageDraw.Draw(im)
    for j, ln in enumerate(lines): d.text((W/2, y0 + j*lh), ln, font=f, fill=(255, 255, 255, 255), anchor='mt')
    y = y0 + len(lines) * lh + 34
    if l.get('small'):
        fs = ImageFont.truetype(SANS, 56)
        for ln in wrap(d, l['small'], fs, 900):
            d.text((W/2, y), ln, font=fs, fill=GOLD, anchor='mt', stroke_width=3, stroke_fill=(0, 0, 0, 170)); y += 74
    # brand header: rule lines + name
    fb = ImageFont.truetype(SANS, 42); tw = d.textlength(ep['brand'], font=fb)
    d.text((W/2, 250), ep['brand'], font=fb, fill=(255, 255, 255, 235), anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0, 120))
    d.line([(W/2 - tw/2 - 90, 250), (W/2 - tw/2 - 24, 250)], fill=GOLD, width=4)
    d.line([(W/2 + tw/2 + 24, 250), (W/2 + tw/2 + 90, 250)], fill=GOLD, width=4)
    d.text((W/2, 305), 'BLESSED PRAYERS', font=ImageFont.truetype(SANS, 30), fill=(255, 255, 255, 170), anchor='mm')
    p = f'{tmp}/card{i}.png'; im.save(p); return p

parts = []
for i, l in enumerate(ep['lines']):
    a, sr = speak(l['say'], ep.get('voice', 'am_michael'), ep.get('speed', 0.94))
    a = np.concatenate([np.zeros(int(sr*0.15), np.float32), a.astype(np.float32), np.zeros(int(sr*0.35), np.float32)])
    wav = f'{tmp}/a{i:02d}.wav'; sf.write(wav, a, sr); D = len(a) / sr
    c = card(i, l); seg = f'{tmp}/s{i:02d}.mp4'
    vf = (f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,"
          f"eq=brightness=-0.08:saturation=1.05,zoompan=z='1+0.0005*on':d=1:s=1080x1920:fps=30,format=yuv420p[bg];"
          f"[1:v]format=rgba,fade=in:st=0:d=0.35:alpha=1[t];[bg][t]overlay=0:0,fade=in:st=0:d=0.25,fade=out:st={D-0.25:.2f}:d=0.25[v]")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-stream_loop', '-1', '-ss', str(l.get('ss', 0)), '-i', f"{FD}/{l['clip']}",
                    '-loop', '1', '-i', c, '-i', wav, '-filter_complex', vf, '-map', '[v]', '-map', '2:a', '-t', f'{D:.3f}',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-maxrate', '3M', '-bufsize', '6M', '-c:a', 'aac', '-ar', '48000', '-ac', '2', seg], check=True)
    parts.append(seg)
lst = f'{tmp}/list.txt'; open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', OUT], check=True)
print('built', OUT)
