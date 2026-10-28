import sys
from PIL import Image
rows = []
for arm in ("base", "still"):
    for kind in ("f", "z"):
        rows.append([f"out/{kind}_{arm}_{t}.png" for t in (2, 7, 12)])
ims = [[Image.open(p) for p in r] for r in rows]
w = max(i.width for r in ims for i in r); h = max(i.height for r in ims for i in r)
canvas = Image.new("RGB", (w * 3, h * len(rows)), (20, 20, 20))
for y, r in enumerate(ims):
    for x, im in enumerate(r):
        canvas.paste(im, (x * w, y * h))
canvas.save("out/grid.png")
print("GRID", canvas.size)
