#!/usr/bin/env python3
"""Animated-scenes picture track for a finished sleep reading.
Usage: build.py SRC_MP4 SCENES_DIR OUT_MP4 [SEG_SECONDS=240] [FADE=10] [FPS=6]
Takes the audio from SRC_MP4 untouched (stream copy), replaces the black screen with
slow-zoom stills that dissolve into each other, dimmed for sleep. Scenes loop to fill the runtime.
The first 60 s keep the title look: scene 1 with the title frame (if TITLE_FRAME env set) fading out."""
import glob, os, subprocess, sys, json
src, scenes_dir, out = sys.argv[1:4]
SEG = float(sys.argv[4]) if len(sys.argv) > 4 else 240.0
FADE = float(sys.argv[5]) if len(sys.argv) > 5 else 10.0
FPS = int(sys.argv[6]) if len(sys.argv) > 6 else 6
DIM = float(os.environ.get("DIM", "-0.12"))          # brightness offset, keeps screen soft at night
W, H = 1920, 1080
dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",src]).decode())
imgs = sorted(glob.glob(os.path.join(scenes_dir, "*.jpg")) + glob.glob(os.path.join(scenes_dir, "*.png")))
assert imgs, "no scene images in " + scenes_dir
n = int((dur + SEG - 1) // (SEG - FADE)) + 1
os.makedirs("segs", exist_ok=True)
segs = []
for i in range(n):
    img = imgs[i % len(imgs)]
    p = f"segs/s{i:04d}.mp4"
    frames = int((SEG) * FPS)
    # alternate zoom in / zoom out and drift direction so neighbours differ
    if i % 2 == 0:
        z = f"min(1.0+0.0004*on,1.25)"
    else:
        z = f"max(1.25-0.0004*on,1.0)"
    x = "iw/2-(iw/zoom/2)" if i % 3 else "(iw-iw/zoom)*on/%d" % frames
    vf = (f"scale=3840:-2,zoompan=z='{z}':x='{x}':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
          f"eq=brightness={DIM}:saturation=0.9,format=yuv420p")
    subprocess.check_call(["ffmpeg","-v","error","-y","-loop","1","-i",img,"-vf",vf,"-frames:v",str(frames),
                           "-c:v","libx264","-preset","veryfast","-crf","28",p])
    segs.append(p)
# chain dissolves
cur = segs[0]; off = 0.0; merged = []
step = 8
for k in range(1, len(segs), step):
    group = segs[k:k+step]
    inputs = [cur] + group
    args = ["ffmpeg","-v","error","-y"]
    for f in inputs: args += ["-i", f]
    fc = []; last = "[0:v]"; t = SEG
    for j in range(1, len(inputs)):
        tag = f"[x{j}]"
        fc.append(f"{last}[{j}:v]xfade=transition=fade:duration={FADE}:offset={t-FADE}{tag}")
        last = tag; t += SEG - FADE
    outp = f"segs/m{k:04d}.mp4"
    args += ["-filter_complex",";".join(fc),"-map",last,"-c:v","libx264","-preset","veryfast","-crf","28",outp]
    subprocess.check_call(args)
    cur = outp
# if only one segment
video = cur
subprocess.check_call(["ffmpeg","-v","error","-y","-i",video,"-i",src,"-map","0:v","-map","1:a","-c:v","copy","-c:a","copy",
                       "-t",str(dur),"-movflags","+faststart",out])
print(json.dumps({"out": out, "duration": dur, "segments": len(segs)}))
