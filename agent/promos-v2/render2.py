# v2 proof-first promo renderer: real screen footage + punch zooms + word-by-word captions + labels.
import sys, os, json, subprocess, numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
POP = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
POPX = "/usr/share/fonts/truetype/google-fonts/Poppins-ExtraBold.ttf"
if not os.path.exists(POPX): POPX = POP
F = lambda p, s: ImageFont.truetype(p, s)
YEL = (255, 214, 10)

def tts_lines(k, lines, voice="am_onyx", gap=0.25):
    """Return audio array, sr, and word timings [(t0,t1,word,line_idx)]."""
    out, words, t, sr = [], [], 0.35, 24000
    out.append(np.zeros(int(sr * .35)))
    for li, ln in enumerate(lines):
        s, sr = k.create(ln, voice=voice, speed=1.05, lang="en-us")
        # trim leading/trailing silence a little
        nz = np.where(np.abs(s) > 0.01)[0]
        if len(nz): s = s[max(0, nz[0] - 600): nz[-1] + 1200]
        dur = len(s) / sr
        ws = ln.split()
        weights = [len(w.strip(",.?!:;")) + 2 for w in ws]
        tot = sum(weights); c = t
        for w_, wt in zip(ws, weights):
            d = dur * wt / tot
            words.append((c, c + d, w_, li)); c += d
        out += [s, np.zeros(int(sr * gap))]
        t += dur + gap
    out.append(np.zeros(int(sr * .6)))
    return np.concatenate(out), sr, words

def read_frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    fr = []
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        fr.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
    return fr

def zoom(img, z, cx=.5, cy=.5):
    if z <= 1.001: return img
    w, h = W / z, H / z
    x0 = min(max(0, cx * W - w / 2), W - w); y0 = min(max(0, cy * H - h / 2), H - h)
    return img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.LANCZOS)

def label(d, text, y, bg=(225, 29, 72), fg=(255, 255, 255), size=40):
    f = F(POP, size); w = f.getlength(text)
    x = (W - w) / 2
    d.rounded_rectangle([x - 26, y - 10, x + w + 26, y + size + 22], radius=18, fill=bg)
    d.text((x, y), text, font=f, fill=fg)

def caption(im, words, t):
    # show the current line's chunk of up to 4 words, current word highlighted yellow
    cur = [i for i, w in enumerate(words) if w[0] <= t < w[1] + .05]
    if not cur: return
    i = cur[0]; li = words[i][3]
    same = [j for j, w in enumerate(words) if w[3] == li]
    groups, g = [], []
    for j in same:
        g.append(j)
        if len(g) == 4 or words[j][2][-1] in ".,?!:": groups.append(g); g = []
    if g: groups.append(g)
    chunk = next(gr for gr in groups if i in gr)
    f = F(POPX, 84)
    d = ImageDraw.Draw(im)
    txt = [words[j][2].upper() for j in chunk]
    widths = [f.getlength(x + " ") for x in txt]
    lines, cur_l, cw = [], [], 0
    for j, x, wd in zip(chunk, txt, widths):
        if cw + wd > W - 140 and cur_l: lines.append(cur_l); cur_l, cw = [], 0
        cur_l.append((j, x, wd)); cw += wd
    lines.append(cur_l)
    y = 1250
    for ln in lines:
        tw = sum(wd for _, _, wd in ln); x = (W - tw) / 2
        for j, word, wd in ln:
            col = YEL if j == i else (255, 255, 255)
            d.text((x, y), word, font=f, fill=col, stroke_width=9, stroke_fill=(0, 0, 0))
            x += wd
        y += 100

def render(spec, k, out):
    audio, sr, words = tts_lines(k, spec["lines"])
    T = len(audio) / sr
    wav = out.replace(".mp4", ".wav"); sf.write(wav, audio, sr)
    reader = {"idx": None, "p": None, "last": None}
    def next_frame(shot, idx):
        if reader["idx"] != idx:
            if reader["p"]: reader["p"].kill()
            reader["p"] = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(shot.get("start", 0)), "-i", shot["clip"], "-vf",
                f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            reader["idx"] = idx
        b = reader["p"].stdout.read(W * H * 3)
        if len(b) == W * H * 3: reader["last"] = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        return reader["last"]
    # shots: list of {"until_line": n, "clip": path, "start": sec, "zoom": [z0,z1], "cy":..., "label": str}
    line_end = {}
    for w in words: line_end[w[3]] = w[1]
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
           "-shortest", "-movflags", "+faststart", out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    endcard = Image.open(spec["endcard"]).convert("RGB").resize((W, H)) if spec.get("endcard") else None
    shot_t0 = {}; imgs = {}
    for n in range(int(T * FPS)):
        t = n / FPS
        idx = next((si for si, s in enumerate(spec["shots"]) if t < line_end.get(s["until_line"], T + 1) + .2), len(spec["shots"]) - 1)
        s = spec["shots"][idx]
        shot_t0.setdefault(idx, t); lt = t - shot_t0[idx]
        if s.get("image"):
            big = imgs.setdefault(s["image"], Image.open(s["image"]).convert("RGB"))
            if big.width != W: big = imgs[s["image"]] = big.resize((W, int(big.height * W / big.width)), Image.LANCZOS)
            rng = max(0, big.height - H); y0, y1 = s.get("pan", [0, 1])
            sd_ = max(.5, line_end.get(s["until_line"], T) - shot_t0[idx]); q = min(1, lt / sd_); q = q * q * (3 - 2 * q)
            y = int(rng * (y0 + (y1 - y0) * q)); im = big.crop((0, y, W, y + H))
        elif s.get("clip"):
            im = Image.fromarray(next_frame(s, idx))
        else:
            im = endcard.copy()
        z0, z1 = s.get("zoom", [1, 1]); sd = max(.5, line_end.get(s["until_line"], T) - shot_t0[idx])
        p = min(1, lt / sd); p = p * p * (3 - 2 * p)
        im = zoom(im, z0 + (z1 - z0) * p, s.get("cx", .5), s.get("cy", .45))
        if lt < .12 and idx > 0:  # quick flash on cut
            im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), .35 * (1 - lt / .12))
        # top darkening for readability
        d = ImageDraw.Draw(im)
        if s.get("hook"):
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            size = s.get("hook_size", 86)
            while max(F(POPX, size).getlength(l) for l in s["hook"]) > W - 110: size -= 4
            f = F(POPX, size); bh = 120 + len(s["hook"]) * (size + 26) + 40
            od.rectangle([0, 0, W, bh], fill=(8, 8, 16, 225)); im.paste(ov, (0, 0), ov); d = ImageDraw.Draw(im)
            y = 130
            for k_, ln in enumerate(s["hook"]):
                w_ = f.getlength(ln); d.text(((W - w_) / 2, y), ln, font=f, fill=YEL if k_ == len(s["hook"]) - 1 else (255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0)); y += size + 26
        if s.get("label"): label(d, s["label"], s.get("label_y", 90))
        if s.get("clip") or s.get("image"): caption(im, words, t)
        pr.stdin.write(im.tobytes())
    pr.stdin.close(); pr.wait()
    return T

if __name__ == "__main__":
    from kokoro_onnx import Kokoro
    k = Kokoro("/home/claude/kk/kokoro-v1.0.onnx", "/home/claude/kk/voices-v1.0.bin")
    spec = json.load(open(sys.argv[1]))
    print(round(render(spec, k, sys.argv[2]), 1), "s")
