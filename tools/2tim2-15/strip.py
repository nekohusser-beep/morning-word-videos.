import sys, subprocess, json
from PIL import Image, ImageDraw
rows = json.loads(sys.argv[2]); out = sys.argv[1]
TW, TH, cols = 200, 113, 7
sh = Image.new("RGB", (cols * TW, len(rows) * (TH + 14)), "black"); d = ImageDraw.Draw(sh)
for r, (clip, t0, step, n) in enumerate(rows):
    for j in range(n):
        t = t0 + j * step; p = f"qc/_s.jpg"
        subprocess.run(f'ffmpeg -v error -y -ss {max(0,t):.3f} -i clips/{clip}.mp4 -frames:v 1 -vf "crop=320:180:200:250,scale={TW}:{TH}" {p}', shell=True)
        x = j * TW; y = r * (TH + 14); sh.paste(Image.open(p), (x, y + 14)); d.text((x + 2, y + 1), f"{clip} {t:.2f}", fill="yellow")
sh.save(out); print(sh.size)
