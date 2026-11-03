"""Remove Grok's burned-in captions from a locked-camera Derrick clip.
Usage: python3 strip_captions.py in.mp4 out.mp4 [y0 y1 x0 x1]
Camera is locked and the chest is nearly static, so a per-pixel low percentile over time (30th) is the
clean plate of the band. Captions only brighten pixels: anything in the band more than DELTA luma above
the plate is caption, dilated 5 px, and replaced by the plate. Audio is copied.
"""
import sys, subprocess, numpy as np
from numpy.lib.stride_tricks import sliding_window_view
src, dst = sys.argv[1], sys.argv[2]
Y0, Y1, X0, X1 = (int(a) for a in sys.argv[3:7]) if len(sys.argv) > 6 else (720, 1080, 60, 660)
DELTA = 28; W, H = 720, 1280
pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
num, den = pr.split("/"); fps = float(num) / float(den)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).copy(); N = len(fr)
band = fr[:, Y0:Y1, X0:X1].astype(np.int16)
luma = band.mean(axis=3)
tot = luma.reshape(N, -1).sum(axis=1)                            # frames with captions are brighter in the band
quiet = np.argsort(tot)[: max(8, N // 4)]                        # the darkest quarter of frames carry no caption
plate = np.median(band[quiet], axis=0).astype(np.int16)          # clean colour per pixel
plate_l = plate.mean(axis=2)
m = (luma - plate_l[None]) > DELTA
def dilate(a, r=5):
    p = np.pad(a, ((0, 0), (r, r), (r, r)))
    v = sliding_window_view(p, (2 * r + 1, 2 * r + 1), axis=(1, 2))
    return v.any(axis=(3, 4))
m = dilate(m)
cnt = m.reshape(N, -1).sum(axis=1)
print(f"{src}: {N} frames, caption px per frame min {cnt.min()} median {int(np.median(cnt))} max {cnt.max()}, frames touched {(cnt > 200).sum()}")
out = fr
pl = plate.astype(np.uint8)
for i in range(N):
    if cnt[i] <= 200: continue
    b = out[i, Y0:Y1, X0:X1]; b[m[i]] = pl[m[i]]
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", f"{fps:.6f}", "-i", "-", "-i", src, "-map", "0:v:0", "-map", "1:a:0?", "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", dst], stdin=subprocess.PIPE)
p.stdin.write(out.tobytes()); p.stdin.close(); p.wait()
print("wrote", dst)
