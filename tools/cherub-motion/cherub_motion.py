#!/usr/bin/env python3
"""Light animation for a 9:16 close-up still. Free, CPU only (numpy + OpenCV + ffmpeg).
Per clip: slow push-in with drift, soft painterly shimmer, local wing/arm/head sway (rotation about a pivot,
feathered mask), twinkling star glints on the brightest highlights, rising gold motes, breathing warm glow.
  cherub_motion.py --img in.jpg --out out.mp4 --secs 5 --glow 0.5:0.2 --limb cx:cy:rx:ry:px:py:deg:hz:phase ...
All coordinates are 0-1 across the frame. Limbs rotate the pixels inside the ellipse about the pivot."""
import argparse, math, subprocess, sys
import cv2, numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--img", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--secs", type=float, default=5.0); ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--zoom", type=float, default=0.07); ap.add_argument("--drift", type=float, default=0.012)
ap.add_argument("--shimmer", type=float, default=3.0, help="painterly shimmer, px at 1080 wide")
ap.add_argument("--glow", default="0.5:0.2"); ap.add_argument("--glowamt", type=float, default=0.11)
ap.add_argument("--glints", type=int, default=8); ap.add_argument("--motes", type=int, default=55)
ap.add_argument("--limb", action="append", default=[])
ap.add_argument("--seed", type=int, default=7); ap.add_argument("--crf", type=int, default=18)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)
W, H, FPS = 1080, 1920, a.fps
N = int(round(a.secs * FPS)); TAU = 2 * math.pi
img = cv2.imread(a.img)
if img.shape[:2] != (H, W): img = cv2.resize(img, (W, H), interpolation=cv2.INTER_LANCZOS4)
imgf = img  # uint8 BGR
# low-res coordinate grids for the displacement fields (upsampled later)
sw, sh = W // 4, H // 4
SY, SX = np.mgrid[0:sh, 0:sw].astype(np.float32)
SXN, SYN = SX / sw, SY / sh
limbs = []
for s in a.limb:
    cx, cy, rx, ry, px, py, deg, hz, ph = [float(v) for v in s.split(":")]
    m = np.exp(-(((SXN - cx) / rx) ** 2 + ((SYN - cy) / ry) ** 2) ** 1.5 * 0.9).astype(np.float32)  # feathered ellipse
    limbs.append(dict(m=m, px=px * sw, py=py * sh, deg=deg, hz=hz, ph=ph))
gx, gy = [float(v) for v in a.glow.split(":")]
# glow sprite (low-res, upsampled once)
GY, GX = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
gr = np.sqrt(((GX / (W / 4) - gx) * 1.0) ** 2 + ((GY / (H / 4) - gy) * 0.56) ** 2)
glow = np.exp(-(gr / 0.34) ** 2).astype(np.float32)
glow = cv2.resize(glow, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
gold = np.array([0.45, 0.80, 1.0], np.float32)  # BGR warm gold
# glint points: brightest local maxima of the blurred luma
luma = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 9)
dil = cv2.dilate(luma, np.ones((71, 71), np.uint8))
cand = np.argwhere((luma >= dil - 1e-3) & (luma > np.percentile(luma, 96)))
cand = sorted(cand.tolist(), key=lambda p: -luma[p[0], p[1]])
pts = []
for y, x in cand:
    if 60 < y < H - 60 and 60 < x < W - 60 and all((y - py) ** 2 + (x - px) ** 2 > 220 ** 2 for py, px in pts):
        pts.append((y, x))
    if len(pts) >= a.glints: break
glint = [dict(y=y, x=x, f=rng.uniform(0.22, 0.45), ph=rng.uniform(0, 1), sz=rng.uniform(26, 58)) for y, x in pts]
motes = dict(x=rng.uniform(0, W, a.motes), y=rng.uniform(0, H, a.motes), v=rng.uniform(14, 44, a.motes),
             r=rng.uniform(1.4, 3.6, a.motes), ph=rng.uniform(0, 1, a.motes), f=rng.uniform(0.3, 0.9, a.motes),
             sw=rng.uniform(5, 18, a.motes), sp=rng.uniform(0.2, 0.5, a.motes))
phi = rng.uniform(0, 1, 6)

def star(size):
    s = int(size) | 1; c = s // 2
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32); dx, dy = xx - c, yy - c
    core = np.exp(-(dx ** 2 + dy ** 2) / (2 * (size * 0.07) ** 2))
    h = np.exp(-(dy / (size * 0.025)) ** 2) * np.exp(-np.abs(dx) / (size * 0.28))
    v = np.exp(-(dx / (size * 0.025)) ** 2) * np.exp(-np.abs(dy) / (size * 0.28))
    return np.clip(core * 1.2 + h + v, 0, 1)
stars = {}
def add_sprite(canvas, spr, x, y, k):
    s = spr.shape[0]; c = s // 2; x0, y0 = int(x) - c, int(y) - c
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + s), min(H, y0 + s)
    if xa >= xb or ya >= yb: return
    canvas[ya:yb, xa:xb] += (spr[ya - y0:yb - y0, xa - x0:xb - x0, None] * gold) * k

cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
       "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out + ".tmp.mp4"]
pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for i in range(N):
    t = i / FPS; u = i / max(1, N - 1)
    ease = u * u * (3 - 2 * u)
    s = 1.0 + a.zoom * ease
    ox = a.drift * W * math.sin(TAU * (0.5 * u + 0.1)); oy = a.drift * H * 0.6 * math.cos(TAU * (0.4 * u))
    # displacement field (low-res, in output pixels at full res)
    A = a.shimmer  # amplitude in full-res px
    dx = (np.sin(TAU * (SYN * 2.1 + t * 0.10 + phi[0])) + 0.6 * np.sin(TAU * (SXN * 3.3 - t * 0.07 + phi[1]))) * A * 0.5
    dy = (np.sin(TAU * (SXN * 2.6 + t * 0.09 + phi[2])) + 0.6 * np.sin(TAU * (SYN * 3.7 + t * 0.06 + phi[3]))) * A * 0.5
    for L in limbs:
        th = math.radians(L["deg"] * math.sin(TAU * L["hz"] * t + L["ph"]))
        rxp, ryp = SX - L["px"], SY - L["py"]
        c, sn = math.cos(-th), math.sin(-th)
        dx = dx + ((c * rxp - sn * ryp) - rxp) * 4.0 * L["m"]
        dy = dy + ((sn * rxp + c * ryp) - ryp) * 4.0 * L["m"]
    DX = cv2.resize(dx.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    DY = cv2.resize(dy.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    gxs = ((np.arange(W, dtype=np.float32) - W / 2) / s + W / 2 + ox)[None, :]
    gys = ((np.arange(H, dtype=np.float32) - H / 2) / s + H / 2 + oy)[:, None]
    mapx = (gxs + DX).astype(np.float32); mapy = (gys + DY).astype(np.float32)
    fr = cv2.remap(imgf, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255.0
    # breathing glow (screen blend)
    g = a.glowamt * (0.65 + 0.35 * math.sin(TAU * t / 4.2 + 0.7))
    lay = glow * gold * g
    fr = 1 - (1 - fr) * (1 - lay)
    # glints + motes (additive)
    add = np.zeros((H, W, 3), np.float32)
    for G in glint:
        k = max(0.0, math.sin(TAU * (G["f"] * t + G["ph"]))) ** 7
        if k < 0.03: continue
        key = int(G["sz"]) | 1
        if key not in stars: stars[key] = star(key)
        add_sprite(add, stars[key], (G["x"] - W / 2 - ox) * s + W / 2, (G["y"] - H / 2 - oy) * s + H / 2, k * 0.95)
    for j in range(a.motes):
        y = (motes["y"][j] - motes["v"][j] * t) % (H + 40) - 20
        x = motes["x"][j] + motes["sw"][j] * math.sin(TAU * motes["sp"][j] * t + motes["ph"][j] * TAU)
        tw = 0.45 + 0.55 * math.sin(TAU * (motes["f"][j] * t + motes["ph"][j])) ** 2
        r = motes["r"][j]; key = ("m", int(r * 10))
        if key not in stars:
            ss = int(r * 9) | 1; yy, xx = np.mgrid[0:ss, 0:ss].astype(np.float32); cc = ss // 2
            stars[key] = np.exp(-((xx - cc) ** 2 + (yy - cc) ** 2) / (2 * (r * 1.1) ** 2))
        add_sprite(add, stars[key], x, y, tw * 0.9)
    fr = np.clip(fr + add, 0, 1)
    pipe.stdin.write((fr * 255).astype(np.uint8).tobytes())
pipe.stdin.close(); pipe.wait()
import os; os.replace(a.out + ".tmp.mp4", a.out)
print("done", a.out, N, "frames", len(glint), "glints")
