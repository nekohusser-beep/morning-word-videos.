"""Encode frames to mp4, print stats, then print small base64 payloads for reading back from the notebook log.
usage: python post.py <comfy_output_dir> <prefix> <input_still> <outdir>"""
import base64, glob, io, os, subprocess, sys
import numpy as np
from PIL import Image
od, prefix, still, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
fs = sorted(glob.glob(os.path.join(od, prefix + "*.png")))
print("FRAMES", len(fs))
if not fs: sys.exit(3)
arr = [np.asarray(Image.open(f).convert("RGB")).astype(np.float32) for f in fs]
h, w = arr[0].shape[:2]
print("SIZE", w, "x", h)
print("MEAN_BRIGHTNESS first/mid/last", round(arr[0].mean(), 1), round(arr[len(arr)//2].mean(), 1), round(arr[-1].mean(), 1))
d = [float(np.abs(arr[i + 1] - arr[i]).mean()) for i in range(len(arr) - 1)]
print("FRAME_DIFF mean/max", round(sum(d) / len(d), 2), round(max(d), 2), "(cherub tool ref 1.3-2.8; frozen 0.01)")
print("FIRST_VS_LAST_DIFF", round(float(np.abs(arr[0] - arr[-1]).mean()), 2))
s = np.asarray(Image.open(still).convert("RGB").resize((w, h), Image.BICUBIC)).astype(np.float32)
print("FIRST_FRAME_VS_INPUT_STILL_DIFF", round(float(np.abs(arr[0] - s).mean()), 2))
print("NAN_OR_BLACK", bool(np.isnan(arr[0]).any() or arr[len(arr)//2].mean() < 3))
tag = os.path.basename(prefix).split("_")[0] if False else prefix
mp4 = os.path.join(out, f"wan22_5b_{tag}.mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(od, prefix + "_%05d_.png"),
                "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", mp4], check=True)
small = os.path.join(out, f"small_{tag}.mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vf", "scale=240:-2", "-c:v", "libx264", "-crf", "34", "-preset", "veryfast",
                "-pix_fmt", "yuv420p", "-an", small], check=True)
print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,r_frame_rate,duration,nb_frames", "-of", "csv=p=0", mp4],
                     capture_output=True, text=True).stdout.strip())
print("MP4_BYTES", os.path.getsize(mp4), "SMALL_BYTES", os.path.getsize(small))
def dump(name, data):
    print("B64START", name); print(base64.encodebytes(data).decode().strip()); print("B64END", name)
for tag2, i in (("f0", 0), ("fmid", len(fs) // 2), ("flast", len(fs) - 1)):
    im = Image.open(fs[i]).convert("RGB"); im.thumbnail((240, 420)); b = io.BytesIO(); im.save(b, "JPEG", quality=62); dump(f"{tag}_{tag2}.jpg", b.getvalue())
dump(f"small_{tag}.mp4", open(small, "rb").read())
