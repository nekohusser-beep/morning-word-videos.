"""Re-check the finished clips in /kaggle/working: metrics + one contact sheet per tag, displayed in the notebook.
usage: python review.py   (run inside the Kaggle notebook after run_test.sh finished)"""
import glob, os, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw
from IPython.display import display

W = "/kaggle/working"
print("FILES", sorted((f, os.path.getsize(os.path.join(W, f))) for f in os.listdir(W) if f.endswith((".mp4", ".jpg", ".png"))))
IN = next(d for d in ("/kaggle/temp/comfy/ComfyUI/input", "/tmp/comfy/ComfyUI/input") if os.path.isdir(d))
STILLS = {"skip": IN + "/skip_fridge.jpg", "derrick": IN + "/derrick_ref.jpg"}
for tag in ("skip", "derrick"):
    mp4 = os.path.join(W, f"wan22_5b_{tag}.mp4")
    if not os.path.exists(mp4):
        print(tag, "NO MP4"); continue
    d = tempfile.mkdtemp()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, os.path.join(d, "f_%03d.png")], check=True)
    fs = sorted(glob.glob(os.path.join(d, "f_*.png")))
    arr = [np.asarray(Image.open(f).convert("RGB")).astype(np.float32) for f in fs]
    df = [float(np.abs(arr[i + 1] - arr[i]).mean()) for i in range(len(arr) - 1)]
    print(f"== {tag}: frames {len(fs)} size {arr[0].shape[1]}x{arr[0].shape[0]}")
    print("   FRAME_DIFF mean/max", round(sum(df) / len(df), 2), round(max(df), 2), "(cherub ref 1.3-2.8, frozen 0.01)")
    print("   FIRST_VS_LAST", round(float(np.abs(arr[0] - arr[-1]).mean()), 2), " BRIGHT f0/mid/last", round(arr[0].mean(), 1), round(arr[len(arr) // 2].mean(), 1), round(arr[-1].mean(), 1))
    print("   NAN_OR_BLACK", bool(any(np.isnan(a).any() or a.mean() < 3 for a in arr)))
    st = STILLS[tag]
    tiles = [Image.open(st).convert("RGB")] + [Image.open(fs[i]).convert("RGB") for i in (0, 12, 24, 36, 48, 60, len(fs) - 1)]
    labels = ["INPUT", "f0", "f12", "f24", "f36", "f48", "f60", "last"]
    tw, th = 180, 312
    sheet = Image.new("RGB", (tw * 4, th * 2), (20, 20, 20))
    for k, (im, lb) in enumerate(zip(tiles, labels)):
        im = im.resize((tw, th), Image.LANCZOS)
        ImageDraw.Draw(im).text((4, 4), lb, fill=(255, 255, 0))
        sheet.paste(im, ((k % 4) * tw, (k // 4) * th))
    out = os.path.join(W, f"sheet_{tag}.jpg")
    sheet.save(out, quality=88)
    print("   sheet", out)
    display(sheet)
