#!/usr/bin/env python3
"""Scene Engine builder (steps 4-5): SCENES.json + ASSETS_DIR -> captioned MP4.

  build.py SCENES.json ASSETS_DIR OUT_DIR [--aspect 16:9|9:16] [--voice af_nicole] [--speed 0.95]
           [--sfx-gain 0.2] [--sfx-all] [--music FILE] [--music-gain 0.12] [--dry-run] [--fps 30]

ASSETS_DIR holds one picture or clip per scene id: s001.png / s001.jpg / s001.mp4 ...
and optionally vo/s001.wav (made with Kokoro when missing).
Voice is the skeleton: each scene lasts as long as its voice clip plus a small pad.
Scenes join with HARD CUTS only (no transitions). Stills get a free ffmpeg motion preset
(push_in, pull_out, pan_right, pan_left, drift_up); an .mp4 asset (e.g. a Gemini clip) is used as is.
Clip sound effects are kept on abstract scenes only, ducked to --sfx-gain (character clips can carry
stray speech). Captions Poppins Bold 52 / bottom margin 205 (9:16), -14 LUFS, true peak under -1 dB.
Outputs in OUT_DIR: <name>.mp4 (captioned, the one to send), <name>_nocaption.mp4, <name>.srt,
timeline.csv (the literal map, also usable in CapCut), contact.jpg, qa.json.
Dry run: placeholder pictures and tone voice, to test the pipeline without credits or Kokoro.
"""
import argparse, csv, glob, json, os, re, shutil, subprocess, sys, wave

ap = argparse.ArgumentParser()
ap.add_argument("scenes"); ap.add_argument("assets"); ap.add_argument("out")
ap.add_argument("--aspect", default=None, choices=["16:9", "9:16"])
ap.add_argument("--voice", default="af_nicole"); ap.add_argument("--speed", type=float, default=0.95)
ap.add_argument("--sfx-gain", type=float, default=0.2); ap.add_argument("--sfx-all", action="store_true")
ap.add_argument("--music"); ap.add_argument("--music-gain", type=float, default=0.12)
ap.add_argument("--fps", type=int, default=30); ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--name", default=None)
A = ap.parse_args()
D = json.load(open(A.scenes)); SC = D["scenes"]
ASPECT = A.aspect or D.get("aspect", "16:9")
W, H = (1920, 1080) if ASPECT == "16:9" else (1080, 1920)
PRX, PRY, FSIZE, MARG = (1280, 720, 40, 50) if ASPECT == "16:9" else (720, 1280, 52, 205)
HEAD, TAIL, FPS = 0.15, 0.35, A.fps
NAME = A.name or re.sub(r"[^A-Za-z0-9]+", "_", D.get("title") or "scene_video").strip("_")
OUT = A.out; TMP = os.path.join(OUT, "work")
for d in (OUT, TMP, os.path.join(TMP, "seg"), os.path.join(TMP, "vo"), os.path.join(TMP, "frames")): os.makedirs(d, exist_ok=True)


def run(cmd, capture=False):
    r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if r.returncode: sys.exit(f"FAILED: {cmd if isinstance(cmd, str) else ' '.join(cmd)}\n{r.stderr[-1500:]}")
    return r.stdout + r.stderr if capture else None


def dur_of(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode())


def has_audio(p):
    return bool(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", p]).decode().strip())


def find_asset(i):
    for ext in ("mp4", "png", "jpg", "jpeg", "webp"):
        p = os.path.join(A.assets, f"{i}.{ext}")
        if os.path.exists(p): return p
    return None


K = None
def tts(text, path):
    global K
    try:
        from kokoro_onnx import Kokoro
        import soundfile as sf
    except ImportError:
        sys.exit("Kokoro not installed: pip install kokoro-onnx soundfile; fetch kokoro-v1.0.onnx and voices-v1.0.bin "
                 "(see .github/workflows/sleep-render.yml), or put your own voice files in ASSETS_DIR/vo/sNNN.wav")
    if K is None:
        d = os.environ.get("KOKORO_DIR", ".")
        K = Kokoro(os.path.join(d, "kokoro-v1.0.onnx"), os.path.join(d, "voices-v1.0.bin"))
    a, sr = K.create(text, voice=A.voice, speed=A.speed, lang="en-us")
    sf.write(path, a, sr)


def placeholder(i, text, path):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (W, H), (244, 236, 216)); dr = ImageDraw.Draw(im)
    try: f = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", H // 14)
    except Exception: f = ImageFont.load_default()
    for k in range(0, W, W // 12): dr.line([(k, 0), (k + H // 3, H)], fill=(225, 214, 190), width=6)
    dr.text((W // 12, H // 3), i, fill=(60, 50, 40), font=f)
    im.save(path)


def motion_filter(m, frames):
    n = max(frames, 2)
    z = {"push_in": f"1.0+0.12*on/{n}", "pull_out": f"1.12-0.12*on/{n}"}.get(m, "1.1")
    x = {"pan_right": f"(iw-iw/zoom)*on/{n}", "pan_left": f"(iw-iw/zoom)*(1-on/{n})"}.get(m, "iw/2-iw/zoom/2")
    y = {"drift_up": f"(ih-ih/zoom)*(1-on/{n})"}.get(m, "ih/2-ih/zoom/2")
    return (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
            f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},format=yuv420p")


# ---------- 1. voice = skeleton ----------
missing, t0, rows, segs = [], 0.0, [], []
for s in SC:
    i = s["id"]
    vo = os.path.join(A.assets, "vo", f"{i}.wav")
    if not os.path.exists(vo):
        vo = os.path.join(TMP, "vo", f"{i}.wav")
        if A.dry_run:
            run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=220:duration={s['est_sec']}", "-af", "volume=0.05", "-ar", "24000", vo])
        else:
            tts(s["vo"], vo)
    vd = dur_of(vo); total = vd + HEAD + TAIL
    if vd > 8.0: print(f"WARN {i}: voice is {vd:.1f}s (over 8 s). Re-split the script line.")
    asset = find_asset(i)
    if asset is None:
        if not A.dry_run: missing.append(i)
        else:
            asset = os.path.join(TMP, f"{i}.png"); placeholder(i, s["vo"][:40], asset)
    segs.append({"s": s, "vo": vo, "vd": vd, "total": total, "asset": asset, "t0": t0})
    t0 += total
if missing: sys.exit(f"Missing pictures/clips for: {', '.join(missing)}. Nothing built.")

# ---------- 2. one segment per scene, hard cuts ----------
for g in segs:
    s, i = g["s"], g["s"]["id"]; tot = g["total"]; frames = int(round(tot * FPS)); out = os.path.join(TMP, "seg", f"{i}.mp4")
    sfx = False
    if g["asset"].endswith(".mp4"):
        vin = ["-i", g["asset"]]
        vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
              f"tpad=stop_mode=clone:stop_duration={tot},trim=duration={tot},setpts=PTS-STARTPTS,format=yuv420p[v]")
        sfx = has_audio(g["asset"]) and (s["kind"] == "abstract" or A.sfx_all)
    else:
        vin = ["-loop", "1", "-t", f"{tot}", "-i", g["asset"]]
        vf = f"[0:v]{motion_filter(s.get('motion', 'push_in'), frames)}[v]"
    fade = f"afade=t=in:d=0.02,afade=t=out:st={tot-0.02:.3f}:d=0.02"
    af = (f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(HEAD*1000)}:all=1,apad=whole_dur={tot}[vo];")
    if sfx:
        af += (f"[0:a]atrim=0:{tot},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,volume={A.sfx_gain},apad=whole_dur={tot}[sf];"
               f"[vo][sf]amix=inputs=2:duration=longest:normalize=0,{fade}[a]")
    else:
        af += f"[vo]{fade}[a]"
    run(["ffmpeg", "-v", "error", "-y", *vin, "-i", g["vo"], "-filter_complex", vf + ";" + af, "-map", "[v]", "-map", "[a]",
         "-t", f"{tot}", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out])
    g["seg"] = out

lst = os.path.join(TMP, "list.txt")
open(lst, "w").write("".join(f"file '{os.path.abspath(g['seg'])}'\n" for g in segs))
RAW = os.path.join(TMP, "raw.mp4")
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", RAW])

# ---------- 3. music bed (optional) and loudness: -14 LUFS, peak under -1 dB ----------
SRC = RAW
if A.music:
    mixed = os.path.join(TMP, "mixed.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", RAW, "-stream_loop", "-1", "-i", A.music, "-filter_complex",
         f"[1:a]aresample=48000,volume={A.music_gain},afade=t=in:d=2[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", mixed]); SRC = mixed


def measure(p, extra=""):
    o = run(["ffmpeg", "-hide_banner", "-i", p, "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json{extra}", "-f", "null", "-"], capture=True)
    return json.loads(o[o.rindex("{"):o.rindex("}") + 1])


m = measure(SRC)
NOCAP = os.path.join(OUT, f"{NAME}_nocaption.mp4")
run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-af",
     f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000",
     "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", NOCAP])
fin = measure(NOCAP)

# ---------- 4. captions: groups of at most 4 words, timed across the voice of each scene ----------
def groups(text):
    w, out, cur = text.split(), [], []
    for x in w:
        cur.append(x)
        if len(cur) >= 4 or re.search(r"[.!?;:,]$", x) and len(cur) >= 2: out.append(cur); cur = []
    if cur:
        if out and len(cur) == 1 and len(out[-1]) < 4: out[-1] += cur
        else: out.append(cur)
    return [" ".join(g) for g in out]


def ats(x): return f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"
def sts(x): return f"{int(x//3600):02d}:{int(x%3600//60):02d}:{x%60:06.3f}".replace(".", ",")


cues = []
for g in segs:
    gs = groups(g["s"]["vo"]); wt = [max(len(x), 1) for x in gs]; tw = sum(wt); a = g["t0"] + HEAD
    for x, ww in zip(gs, wt):
        b = a + g["vd"] * ww / tw; cues.append([a, b, x]); a = b
for k in range(len(cues) - 1):
    cues[k][1] = min(cues[k][1], cues[k + 1][0] - 0.02)
ass = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {PRX}\nPlayResY: {PRY}\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
       "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
       f"Style: Cap,Poppins,{FSIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4.2,0,2,40,40,{MARG},1\n\n"
       "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
ass += "".join(f"Dialogue: 0,{ats(a)},{ats(b)},Cap,,0,0,0,,{t}\n" for a, b, t in cues)
ASS = os.path.join(TMP, "caps.ass"); open(ASS, "w").write(ass)
with open(os.path.join(OUT, f"{NAME}.srt"), "w") as f:
    for n, (a, b, t) in enumerate(cues, 1): f.write(f"{n}\n{sts(a)} --> {sts(b)}\n{t}\n\n")
FINAL = os.path.join(OUT, f"{NAME}.mp4")
fd = next((d for d in ("/usr/share/fonts/truetype/google-fonts", os.path.join(os.path.dirname(__file__), "fonts"), "fonts") if os.path.isdir(d)), ".")
run(["ffmpeg", "-v", "error", "-y", "-i", NOCAP, "-vf", f"ass={ASS}:fontsdir={fd}", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
     "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", FINAL])

# ---------- 5. literal map, contact sheet, QA ----------
with open(os.path.join(OUT, "timeline.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["scene", "start", "end", "kind", "asset", "motion", "vo", "image_prompt"])
    for g in segs:
        s = g["s"]; w.writerow([s["id"], f"{g['t0']:.2f}", f"{g['t0']+g['total']:.2f}", s["kind"], os.path.basename(g["asset"]), s.get("motion", ""), s["vo"], s.get("image_prompt", "")])
for n, g in enumerate(segs, 1):
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{g['total']*0.4:.2f}", "-i", g["seg"], "-frames:v", "1", "-vf", "scale=360:-2", os.path.join(TMP, "frames", f"f{n:03d}.jpg")])
cols = 6; rows_n = -(-len(segs) // cols)
run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", os.path.join(TMP, "frames", "f%03d.jpg"), "-vf", f"tile={cols}x{rows_n}", "-frames:v", "1", os.path.join(OUT, "contact.jpg")])
ab = sum(1 for g in segs if g["s"]["kind"] == "abstract")
qa = {"final": FINAL, "dry_run": A.dry_run, "aspect": ASPECT, "scenes": len(segs), "duration_sec": round(dur_of(FINAL), 1),
      "longest_voice_sec": round(max(g["vd"] for g in segs), 2), "scenes_over_8s": [g["s"]["id"] for g in segs if g["vd"] > 8.0],
      "abstract_pct": round(100 * ab / len(segs)), "loudness_lufs": fin["input_i"], "true_peak_db": fin["input_tp"],
      "loudness_ok": abs(float(fin["input_i"]) + 14) <= 1.0 and float(fin["input_tp"]) <= -1.0,
      "todo_before_posting": ["Neko's yes on this exact file", "AI disclosure flag on YouTube (altered/synthetic), TikTok (AI-generated), Instagram (AI info)",
                              "listen to the joins and the scripture lines; transcript check of the audio against the script"]}
json.dump(qa, open(os.path.join(OUT, "qa.json"), "w"), indent=1)
print(json.dumps(qa, indent=1))
