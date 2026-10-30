#!/usr/bin/env python3
"""Scene motion: turns still paintings into slow living scenes. Free, CPU only (numpy + OpenCV + ffmpeg).

Effects per scene: slow push-in with a tiny drift, soft drifting flow warp (clouds, water, mist),
twinkle on the brightest light (crystal, jewels, gold), a breathing glow at the light source,
drifting gold motes, and soft dissolves between scenes.

  python3 scene_motion.py --scene still1.jpg:11:0.5:0.35:water --scene still2.jpg:11:0.5:0.4:sky --out out.mp4

--scene is  image:seconds:glowx:glowy:flow   (glow x/y are 0-1 across the frame; flow = water | sky | full | none)
"""
import argparse
import math
import subprocess
import sys

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--scene", action="append", required=True, help="image:seconds:glowx:glowy:flow")
ap.add_argument("--out", required=True)
ap.add_argument("--w", type=int, default=1280)
ap.add_argument("--h", type=int, default=720)
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--xfade", type=float, default=2.0)
ap.add_argument("--zoom", type=float, default=0.06, help="total push-in over one scene (0.06 = 6 percent)")
ap.add_argument("--flow", type=float, default=4.0, help="flow warp amplitude in pixels at 1280 wide")
ap.add_argument("--twinkle", type=float, default=0.12, help="how much the brightest light shimmers (0 to 0.3)")
ap.add_argument("--glow", type=float, default=0.09, help="glow strength")
ap.add_argument("--motes", type=int, default=45, help="gold motes per scene")
ap.add_argument("--audio", default="", help="optional audio file laid under the video")
ap.add_argument("--crf", type=int, default=23)
ap.add_argument("--limit", type=float, default=0.0, help="render only the first N seconds")
a = ap.parse_args()

W, H, FPS, XF = a.w, a.h, a.fps, a.xfade
AMP = a.flow * W / 1280.0
TAU = 2 * math.pi
Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
YN, XN = Y / H, X / W


def smooth(v, lo, hi):
    t = np.clip((v - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def flow_mask(mode):
    if mode == "water":
        return (0.30 + 0.90 * smooth(YN, 0.58, 0.75)).astype(np.float32)
    if mode == "sky":
        return (0.15 + 0.90 * (1 - smooth(YN, 0.45, 0.70))).astype(np.float32)
    if mode == "full":
        return np.full((H, W), 0.7, np.float32)
    return np.zeros((H, W), np.float32)


class Scene:
    def __init__(self, spec, idx):
        parts = spec.split(":")
        self.path = parts[0]
        self.dur = float(parts[1])
        self.gx = float(parts[2]) if len(parts) > 2 else 0.5
        self.gy = float(parts[3]) if len(parts) > 3 else 0.35
        self.mode = parts[4] if len(parts) > 4 else "full"
        im = cv2.imread(self.path, cv2.IMREAD_COLOR)
        if im is None:
            sys.exit(f"cannot read {self.path}")
        self.bw, self.bh = int(W * 1.12), int(H * 1.12)
        self.base = cv2.resize(im, (self.bw, self.bh), interpolation=cv2.INTER_AREA)
        flat = cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)
        lum = cv2.cvtColor(flat, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        self.bright = (np.clip((lum - 0.62) / 0.38, 0, 1) ** 1.5).astype(np.float32)
        rng = np.random.default_rng(100 + idx)
        coarse = rng.random((14, 24)).astype(np.float32) * TAU
        self.phase = cv2.resize(coarse, (W, H), interpolation=cv2.INTER_CUBIC)
        self.mask = flow_mask(self.mode)
        d2 = (XN - self.gx) ** 2 * (W / H) ** 2 + (YN - self.gy) ** 2
        self.glow = np.exp(-d2 / (2 * 0.22 ** 2)).astype(np.float32)
        self.mx = rng.random(a.motes)
        self.my = rng.random(a.motes)
        self.ms = 0.012 + 0.02 * rng.random(a.motes)
        self.mp = rng.random(a.motes) * TAU
        self.mr = 1 + (rng.random(a.motes) * 2).astype(int)
        self.px = (rng.random() - 0.5) * 0.02 * self.bw
        self.py = (rng.random() - 0.5) * 0.012 * self.bh

    def frame(self, t):
        p = min(max(t / self.dur, 0.0), 1.0)
        z = 1 + a.zoom * p
        cw, ch = self.bw / z, self.bh / z
        x0 = (self.bw - cw) / 2 + (p - 0.5) * self.px
        y0 = (self.bh - ch) / 2 + (p - 0.5) * self.py
        M = np.float32([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
        f = cv2.warpAffine(self.base, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        if AMP > 0 and self.mode != "none":
            dx = AMP * 0.5 * (np.sin(TAU * (YN * 3.0 + t / 7.0)) + np.sin(TAU * (XN * 2.0 - t / 9.0))) * self.mask
            dy = AMP * 0.6 * np.cos(TAU * (XN * 3.0 + YN + t / 8.0)) * self.mask
            f = cv2.remap(f, X + dx, Y + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        f = f.astype(np.float32)
        gain = 1.0 + a.twinkle * self.bright * np.sin(TAU * 0.45 * t + self.phase)
        f *= gain[..., None]
        pulse = a.glow * (1 + 0.55 * math.sin(TAU * t / 6.0 + self.gx * 5))
        f += self.glow[..., None] * pulse * np.array([110, 185, 255], np.float32)
        layer = np.zeros((H, W), np.uint8)
        for i in range(len(self.mx)):
            yy = (self.my[i] - self.ms[i] * t) % 1.0
            xx = self.mx[i] + 0.02 * math.sin(TAU * t / 9.0 + self.mp[i])
            cv2.circle(layer, (int(xx * W), int(yy * H)), int(self.mr[i] * W / 1280), 255, -1, cv2.LINE_AA)
        if len(self.mx):
            layer = cv2.GaussianBlur(layer, (0, 0), 1.2).astype(np.float32) / 255.0
            tw = 0.55 + 0.45 * np.sin(TAU * t / 3.0 + 0.0)
            f += layer[..., None] * 150 * tw * np.array([0.55, 0.85, 1.0], np.float32)
        return np.clip(f, 0, 255).astype(np.uint8)


scenes = [Scene(s, i) for i, s in enumerate(a.scene)]
starts = []
cur = 0.0
for s in scenes:
    starts.append(cur)
    cur += s.dur - XF
total = cur + XF
if a.limit:
    total = min(total, a.limit)


def frame_at(t):
    live = [i for i, s in enumerate(scenes) if starts[i] <= t < starts[i] + s.dur]
    if not live:
        live = [len(scenes) - 1]
    if len(live) == 1:
        i = live[0]
        return scenes[i].frame(t - starts[i])
    i, j = live[0], live[-1]
    w = (t - starts[j]) / XF
    w = w * w * (3 - 2 * w)
    fa = scenes[i].frame(t - starts[i]).astype(np.float32)
    fb = scenes[j].frame(t - starts[j]).astype(np.float32)
    return np.clip(fa * (1 - w) + fb * w, 0, 255).astype(np.uint8)


tmp = a.out + ".part.mp4"
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
if a.audio:
    cmd += ["-i", a.audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k", "-shortest"]
cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp]
pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
n = int(total * FPS)
for k in range(n):
    pr.stdin.write(frame_at(k / FPS).tobytes())
    if k % (FPS * 5) == 0:
        print(f"{k / FPS:6.1f}s / {total:.1f}s", flush=True)
pr.stdin.close()
if pr.wait() != 0:
    sys.exit("ffmpeg failed")
import os
os.replace(tmp, a.out)
print("done", a.out)
