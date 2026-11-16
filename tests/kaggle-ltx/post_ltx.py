"""Mux LTX frames + audio into mp4, print stats, make a contact sheet, push to the public repo via the Kaggle secret GITHUB_TOKEN if attached.
usage: python post_ltx.py <comfy_output_dir> <prefix> <outdir>"""
import glob, json, os, shutil, subprocess, sys, time
import numpy as np
from PIL import Image
od, prefix, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
fs = sorted(glob.glob(os.path.join(od, prefix + "_*.png")))
print("FRAMES", len(fs))
if not fs: sys.exit(3)
arr = [np.asarray(Image.open(f).convert("RGB")).astype(np.float32) for f in fs]
h, w = arr[0].shape[:2]
d = [float(np.abs(arr[i + 1] - arr[i]).mean()) for i in range(len(arr) - 1)]
print("SIZE", w, "x", h, "MEAN_BRIGHTNESS first/mid/last", round(arr[0].mean(), 1), round(arr[len(arr)//2].mean(), 1), round(arr[-1].mean(), 1))
print("FRAME_DIFF mean/max", round(sum(d) / len(d), 2), round(max(d), 2), "(frozen = 0.01)")
print("NAN_OR_BLACK", bool(np.isnan(arr[0]).any() or arr[len(arr)//2].mean() < 3))
fps = os.environ.get("FPS", "24")
audio = sorted(glob.glob(os.path.join(od, "audio", os.path.dirname(prefix), "*.flac")) + glob.glob(os.path.join(od, "audio", "*.flac")))
print("AUDIO", audio[-1:] )
stamp = time.strftime("%Y%m%d_%H%M", time.gmtime())
mp4 = os.path.join(out, f"ltx23_verse_bg_{stamp}.mp4")
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", fps, "-i", os.path.join(od, prefix + "_%05d_.png")]
if audio: cmd += ["-i", audio[-1], "-c:a", "aac", "-b:a", "160k", "-shortest"]
cmd += ["-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", mp4]
subprocess.run(cmd, check=True)
print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,r_frame_rate,duration", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout.strip())
print("MP4_BYTES", os.path.getsize(mp4))
sheet = os.path.join(out, f"ltx23_sheet_{stamp}.jpg")
idx = [0, len(fs)//3, 2*len(fs)//3, len(fs)-1]; ims = []
for i in idx:
    im = Image.open(fs[i]).convert("RGB"); im.thumbnail((270, 480)); ims.append(im)
S = Image.new("RGB", (sum(i.width for i in ims), ims[0].height)); x = 0
for im in ims: S.paste(im, (x, 0)); x += im.width
S.save(sheet, quality=80)
try:
    from kaggle_secrets import UserSecretsClient
    tok = UserSecretsClient().get_secret("GITHUB_TOKEN")
except Exception as e:
    print("NO_SECRET", repr(e)[:200]); sys.exit(0)
def sh(c, env=None):
    r = subprocess.run(c, shell=True, capture_output=True, text=True, env=env); return (r.stdout + r.stderr).strip()
sh("rm -rf hw; git clone --depth 1 https://github.com/nekohusser-beep/morning-word-videos. hw 2>&1 | tail -1")
dst = "hw/episodes/ltx"; os.makedirs(dst, exist_ok=True)
for f in (mp4, sheet): shutil.copy(f, dst)
shutil.copy("/kaggle/temp/ltx/mem.log", dst + f"/mem_{stamp}.log") if os.path.exists("/kaggle/temp/ltx/mem.log") else None
sh(f"cd hw && git add episodes/ltx && git -c user.name=kaggle-handoff -c user.email=kaggle@example.invalid commit -qm 'LTX-2.3 test clip {stamp} (Kaggle T4)'")
e2 = dict(os.environ); e2["GIT_TERMINAL_PROMPT"] = "0"
print("PUSH", sh('cd hw && git push https://x-access-token:%s@github.com/nekohusser-beep/morning-word-videos. HEAD:main 2>&1 | sed "s/%s/***/g" | tail -3' % (tok, tok), env=e2))
