"""Eye-openness per frame for a locked-camera Derrick clip: share of bright, low-saturation (sclera) pixels in both eye boxes."""
import cv2, numpy as np, sys
BOX = [(320, 360, 380, 398), (420, 360, 478, 398)]
def series(path):
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS) or 24; out = []; i = 0
    while True:
        ok, fr = cap.read()
        if not ok: break
        hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV); tot = 0; n = 0
        for x0, y0, x1, y1 in BOX:
            r = hsv[y0:y1, x0:x1]; m = (r[..., 2] > 150) & (r[..., 1] < 85); tot += m.sum(); n += m.size
        out.append((i / fps, tot / n)); i += 1
    return out
if __name__ == "__main__":
    for t, v in series(sys.argv[1])[: int(sys.argv[2]) if len(sys.argv) > 2 else 400]: print(f"{t:5.2f} {v:.3f} " + "#" * int(v * 200))
