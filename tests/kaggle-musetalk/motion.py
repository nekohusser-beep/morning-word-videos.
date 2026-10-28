# Motion and sharpness stats for the two MuseTalk arms (reads out/small_*.mp4, 360x640).
import cv2, numpy as np, sys
O = "/kaggle/working/t/out/"
# bands in 360x640 coordinates (x0, x1, y0, y1)
BANDS = {
    "upper_face(hair/eyes)": {"base": (90, 270, 190, 250), "still": (90, 270, 130, 190)},
    "mouth_box": {"base": (107, 267, 272, 392), "still": (107, 267, 182, 302)},
    "background_left": {"base": (0, 60, 100, 500), "still": (0, 60, 100, 500)},
}
def load(p):
    c = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = c.read()
        if not ok: break
        fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32))
    return np.array(fr), c.get(cv2.CAP_PROP_FPS)
for arm in ("base", "still"):
    fr, fps = load(O + "small_%s.mp4" % arm)
    print("ARM", arm, "frames", len(fr), "fps", fps, "seconds %.2f" % (len(fr) / fps))
    d = np.abs(np.diff(fr, axis=0))
    for name, boxes in BANDS.items():
        x0, x1, y0, y1 = boxes[arm]
        m = d[:, y0:y1, x0:x1].mean(axis=(1, 2))
        sh = [cv2.Laplacian(f[y0:y1, x0:x1], cv2.CV_32F).var() for f in fr[::10]]
        print("  %-24s mean frame-diff %.2f  max %.2f  sharp(lapvar) %.0f" % (name, m.mean(), m.max(), np.mean(sh)))
    g = d.mean(axis=(1, 2))
    per_sec = [round(float(g[i:i + int(fps)].mean()), 2) for i in range(0, len(g), int(fps))]
    print("  whole-frame diff per second:", per_sec)
    top = np.argsort(g)[-3:][::-1]
    print("  biggest jumps at seconds:", [round(float((i + 1) / fps), 2) for i in top], [round(float(g[i]), 2) for i in top])
