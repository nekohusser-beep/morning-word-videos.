# Download MuseTalk 1.5 weights into ./models (run from the MuseTalk folder with the Python 3.10 env)
import os, sys, urllib.request
from huggingface_hub import hf_hub_download
M = "models"
def hf(repo, files, sub="."):
    for fn in files:
        p = hf_hub_download(repo, fn, local_dir=os.path.join(M, sub))
        print("OK", repo, fn, os.path.getsize(p), flush=True)
hf("TMElyralab/MuseTalk", ["musetalkV15/musetalk.json", "musetalkV15/unet.pth"])
hf("stabilityai/sd-vae-ft-mse", ["config.json", "diffusion_pytorch_model.bin"], "sd-vae")
hf("openai/whisper-tiny", ["config.json", "pytorch_model.bin", "preprocessor_config.json"], "whisper")
hf("yzd-v/DWPose", ["dw-ll_ucoco_384.pth"], "dwpose")
os.makedirs(os.path.join(M, "face-parse-bisent"), exist_ok=True)
r18 = os.path.join(M, "face-parse-bisent", "resnet18-5c106cde.pth")
if not os.path.exists(r18):
    urllib.request.urlretrieve("https://download.pytorch.org/models/resnet18-5c106cde.pth", r18)
print("OK resnet18", os.path.getsize(r18), flush=True)
fp = os.path.join(M, "face-parse-bisent", "79999_iter.pth")
if not os.path.exists(fp):
    try:
        import gdown
        gdown.download(id="154JgKpzCPW82qINcVieuPH3fZ2e0P812", output=fp, quiet=True)
    except Exception as e:
        print("gdown failed:", e, flush=True)
    if not os.path.exists(fp) or os.path.getsize(fp) < 1000000:
        print("trying HF fallback for face-parse", flush=True)
        hf("ManyOtherFunctions/face-parse-bisent", ["79999_iter.pth"], "face-parse-bisent")
print("OK face-parse", os.path.getsize(fp), flush=True)
print("WEIGHTS DONE")
