"""Cut the subject out of an image (rembg, MIT, danielgatis/rembg; u2net model, CPU, ~1 s/image, $0).
Use on the clean Flow/OpenArt art BEFORE text goes on: thumbnails, Etsy mockups, community-post graphics.
  pip install --break-system-packages "rembg[cpu]==2.0.67"
  python3 tools/thumbs/cutout.py in.jpg [more.jpg ...]   -> in-cut.png (transparent background)
Model choices: u2net (default, general), isnet-general-use (finer edges), u2net_human_seg (people).
"""
import sys, os
from rembg import remove, new_session
from PIL import Image
model = os.environ.get("REMBG_MODEL", "u2net")
s = new_session(model)
for p in sys.argv[1:]:
    out = os.path.splitext(p)[0] + "-cut.png"
    remove(Image.open(p).convert("RGB"), session=s).save(out)
    print(out)
