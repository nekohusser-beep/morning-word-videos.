#!/usr/bin/env python3
"""Animate still scenes under a sung track: slow zoom/drift, breathing light at the light source, golden motes, soft dissolves.
Free: Python + OpenCV + numpy + ffmpeg only. No faces are drawn here; the stills are the person's own originals.

Usage:
  build.py --audio song.mp3 --scenes v1.jpg,v2.jpg,... --cuts 22.8,58.4,94.0,151.6,196.2 --out out.mp4 [--w 1920 --h 1080 --fps 30 --xfade 3.0]
  --cuts = the times (seconds) where the picture dissolves to the next scene (len(scenes)-1 values).
  --glows = optional "x:y,x:y,..." (fractions) where the light source sits in each scene (default centre-top).
Audio is copied in as AAC with a short fade in/out; picture length = audio length.
"""
import argparse
import math
import subprocess

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--audio", required=True)
ap.add_argument("--scenes", required=True)
ap.add_argument("--cuts", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--glows", default="")
ap.add_argument("--w", type=int, default=1920)
ap.add_argument("--h", type=int, default=1080)
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--xfade", type=float, default=3.0)
ap.add_argument("--limit", type=float, default=0.0, help="render only the first N seconds (preview)")
ap.add_argument("--loop", type=float, default=0.0, help="make a seamless loop: crossfade the last N s of the song into its start, dissolve the last scene back into the first, no fades")
ap.add_argument("--crf", type=int, default=21)
ap.add_argument("--maxrate", default="", help="e.g. 1500k (adds a bitrate cap)")
ap.add_argument("--audio-out", default="", help="write the (loop) audio used, as wav")
a = ap.parse_args()

W, H, FPS, XF = a.w, a.h, a.fps, a.xfade
scenes = a.scenes.split(",")
cuts = [float(x) for x in a.cuts.split(",") if x]
assert len(cuts) == len(scenes) - 1, "need len(scenes)-1 cuts"
dur = float(
    subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.audio], text=True
    ).strip()
)
LOOP = a.loop > 0
SRA = 44100
audio_path = a.audio
if LOOP:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.audio, "-f", "f32le", "-ac", "2", "-ar", str(SRA), "-"], capture_output=True, check=True).stdout
    au = np.frombuffer(raw, np.float32).reshape(-1, 2)
    X = int(a.loop * SRA)
    Ln = len(au) - X
    loop_au = au[:Ln].copy()
    th = np.linspace(0, np.pi / 2, X)[:, None]
    loop_au[:X] = au[:X] * np.sin(th) + au[Ln:Ln + X] * np.cos(th)  # tail fades out while the head fades in: the join is the song continuing into its own intro
    import wave
    audio_path = a.audio_out or (a.out + ".loop.wav")
    with wave.open(audio_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SRA)
        wf.writeframes((np.clip(loop_au, -1, 1) * 32767).astype("<i2").tobytes())
    dur = Ln / SRA
total = a.limit or dur
bounds = [0.0] + cuts + [dur]
glow_pts = [tuple(float(v) for v in g.split(":")) for g in a.glows.split(",")] if a.glows else [(0.5, 0.3)] * len(scenes)

# per-scene camera move: (zoom start, zoom end, pan x start/end, pan y start/end) as fractions of the spare room
MOVES = [
    (1.00, 1.09, 0.3, 0.7, 0.8, 0.3),
    (1.09, 1.00, 0.7, 0.3, 0.4, 0.6),
    (1.00, 1.10, 0.5, 0.5, 0.9, 0.2),
    (1.08, 1.00, 0.2, 0.6, 0.3, 0.5),
    (1.00, 1.08, 0.7, 0.3, 0.5, 0.5),
    (1.10, 1.00, 0.5, 0.5, 0.6, 0.2),
]

imgs = []
for p in scenes:
    im = cv2.imread(p, cv2.IMREAD_COLOR)
    assert im is not None, p
    s = max(W * 1.25 / im.shape[1], 1e-6)  # work copy ~1.25x output width for clean subpixel scaling
    im = cv2.resize(im, (int(im.shape[1] * s), int(im.shape[0] * s)), interpolation=cv2.INTER_AREA)
    imgs.append(im)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vig = 1.0 - 0.16 * np.clip(((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2) * 2.2, 0, 1)
vig = vig[..., None].astype(np.float32)
glows = []
for gx, gy in glow_pts:
    d2 = ((xx / W - gx) ** 2 * (W / H) ** 2 + (yy / H - gy) ** 2)
    glows.append(np.exp(-d2 / 0.045).astype(np.float32)[..., None])
WARM = np.array([0.55, 0.85, 1.0], np.float32)  # BGR, warm gold

rng = np.random.default_rng(23)
NP = 70
px = rng.random(NP)
py = rng.random(NP)
ncy = rng.integers(4, 11, NP)  # whole drift cycles per loop so the sparks are in the same place at the end as at the start
msw = rng.integers(20, 60, NP)
mtw = rng.integers(80, 200, NP)
pr = 2 + 5 * rng.random(NP)
pph = rng.random(NP) * 6.28
sprite = {}
for r in range(2, 8):
    k = r * 4 + 1
    g = cv2.getGaussianKernel(k, r * 0.9)
    sprite[r] = (g @ g.T / (g @ g.T).max()).astype(np.float32)


def scene_frame(i, t):
    """frame of scene i at global time t, camera move spanning the scene plus half a dissolve either side"""
    t0, t1 = bounds[i] - XF / 2, bounds[i + 1] + XF / 2
    u = min(max((t - t0) / (t1 - t0), 0.0), 1.0)
    u = u * u * (3 - 2 * u) * 0.35 + u * 0.65  # gentle ease
    z0, z1, ax0, ax1, ay0, ay1 = MOVES[i % len(MOVES)]
    z = z0 + (z1 - z0) * u
    im = imgs[i]
    ih, iw = im.shape[:2]
    cw, ch = iw / z, iw / z * H / W
    if ch > ih:
        ch = ih / z
        cw = ch * W / H
    fx = ax0 + (ax1 - ax0) * u
    fy = ay0 + (ay1 - ay0) * u
    x0 = (iw - cw) * fx
    y0 = (ih - ch) * fy
    sc = W / cw
    M = np.array([[sc, 0, -x0 * sc], [0, sc, -y0 * sc]], np.float32)
    f = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    # breathing light at the source
    breath = 0.10 + 0.05 * math.sin(2 * math.pi * max(1, round(dur / 7.0)) * t / dur + i)
    f += glows[i] * WARM * 255.0 * breath
    return f


def motes(f, t):
    for k in range(NP):
        ph = t / dur
        y = (py[k] - ncy[k] * ph) % 1.0
        x = (px[k] + 0.02 * math.sin(2 * math.pi * msw[k] * ph + pph[k])) % 1.0
        r = int(pr[k]) if int(pr[k]) in sprite else 3
        tw = 0.35 + 0.35 * math.sin(2 * math.pi * mtw[k] * ph + pph[k])
        sp = sprite[r]
        cx, cy = int(x * W), int(y * H)
        h = sp.shape[0] // 2
        x0, x1, y0, y1 = cx - h, cx + h + 1, cy - h, cy + h + 1
        if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
            continue
        f[y0:y1, x0:x1] += sp[..., None] * WARM * 255.0 * tw * 0.55
    return f


def frame_at(t):
    i = 0
    while i < len(cuts) and t >= cuts[i]:
        i += 1
    f = scene_frame(i, t)
    # dissolve to the neighbour inside the half-xfade window around a cut
    if i > 0 and t < cuts[i - 1] + XF / 2:
        w = (t - (cuts[i - 1] - XF / 2)) / XF
        w = w * w * (3 - 2 * w)
        f = scene_frame(i - 1, t) * (1 - w) + f * w
    elif i < len(cuts) and t > cuts[i] - XF / 2:
        w = (t - (cuts[i] - XF / 2)) / XF
        w = w * w * (3 - 2 * w)
        f = f * (1 - w) + scene_frame(i + 1, t) * w
    if LOOP and t > dur - XF:
        w = (t - (dur - XF)) / XF
        w = w * w * (3 - 2 * w)
        f = scene_frame(len(cuts), t) * (1 - w) + scene_frame(0, t - dur) * w
    f = motes(f * vig, t)
    fade = 1.0 if LOOP else min(1.0, t / 2.0, max(0.0, (total - t) / 3.0))
    return np.clip(f * fade, 0, 255).astype(np.uint8)


cmd = [
    "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", audio_path, "-t", f"{total:.3f}",
    *([] if LOOP else ["-af", f"afade=t=in:d=1.5,afade=t=out:st={max(total - 3.5, 0):.2f}:d=3.5"]),
    "-c:v", "libx264", "-preset", "veryfast", "-crf", str(a.crf), *(["-maxrate", a.maxrate, "-bufsize", str(int(a.maxrate.rstrip("k")) * 2) + "k"] if a.maxrate else []),
    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    "-c:a", "aac", "-b:a", "192k", "-shortest", a.out,
]
pr_ = subprocess.Popen(cmd, stdin=subprocess.PIPE)
n = int(total * FPS)
for k in range(n):
    pr_.stdin.write(frame_at(k / FPS).tobytes())
    if k % (FPS * 20) == 0:
        print(f"{k / FPS:6.1f}s / {total:.1f}s", flush=True)
pr_.stdin.close()
pr_.wait()
print("done", a.out)
