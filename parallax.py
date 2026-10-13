import sys, glob, os, numpy as np, cv2, subprocess
from PIL import Image
from transformers import pipeline
pipe = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
os.makedirs("anim", exist_ok=True)
W, H, FPS, DUR = 720, 1280, 30, 5.0
for p in sorted(glob.glob("stills/*.png")):
    name = os.path.basename(p)[:-4]
    img = Image.open(p).convert("RGB")
    # cover-fit to 1.15x canvas so motion never shows edges
    S = 1.15; tw, th = int(W*S), int(H*S)
    r = max(tw/img.width, th/img.height)
    img = img.resize((int(img.width*r)+1, int(img.height*r)+1), Image.LANCZOS)
    l = (img.width-tw)//2; t = (img.height-th)//2
    img = img.crop((l, t, l+tw, t+th))
    d = np.array(pipe(img)["depth"].resize((tw, th)), dtype=np.float32)
    d = cv2.GaussianBlur(d, (0, 0), 6); d = (d-d.min())/(d.max()-d.min()+1e-6)  # 1 = near
    src = np.array(img)[:, :, ::-1]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = tw/2, th/2
    n = int(DUR*FPS)
    out = f"anim/{name}.mp4"
    proc = subprocess.Popen(f"ffmpeg -v error -y -f rawvideo -pix_fmt bgr24 -s {W}x{H} -r {FPS} -i - -c:v libx264 -crf 17 -pix_fmt yuv420p {out}".split(), stdin=subprocess.PIPE)
    for i in range(n):
        k = i/(n-1); e = float(0.5-0.5*np.cos(np.pi*k))  # ease in-out
        zoom = 1.0 + 0.05*e                       # gentle dolly-in
        par = 18*e                                # parallax px for nearest layer
        # sample coordinates into the oversized source
        sx = (xx - W/2)/zoom + cx
        sy = (yy - H/2)/zoom + cy
        dd = cv2.remap(d, sx.astype(np.float32), sy.astype(np.float32), cv2.INTER_LINEAR)
        # near objects drift/scale more than far ones
        sx2 = sx - (sx-cx)*0.035*e*dd - par*0.25*dd
        sy2 = sy - (sy-cy)*0.035*e*dd + par*0.10*dd
        f = cv2.remap(src, sx2.astype(np.float32), sy2.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        proc.stdin.write(f.tobytes())
    proc.stdin.close(); proc.wait(); print("ok", out)
