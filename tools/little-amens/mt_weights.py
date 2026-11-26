import os, subprocess
from huggingface_hub import hf_hub_download
M='models'
for d in ['musetalk','musetalkV15','syncnet','dwpose','face-parse-bisent','sd-vae','whisper']: os.makedirs(f'{M}/{d}',exist_ok=True)
G=[('TMElyralab/MuseTalk','musetalk/musetalk.json',M),('TMElyralab/MuseTalk','musetalk/pytorch_model.bin',M),
   ('TMElyralab/MuseTalk','musetalkV15/musetalk.json',M),('TMElyralab/MuseTalk','musetalkV15/unet.pth',M),
   ('stabilityai/sd-vae-ft-mse','config.json',M+'/sd-vae'),('stabilityai/sd-vae-ft-mse','diffusion_pytorch_model.bin',M+'/sd-vae'),
   ('openai/whisper-tiny','config.json',M+'/whisper'),('openai/whisper-tiny','pytorch_model.bin',M+'/whisper'),('openai/whisper-tiny','preprocessor_config.json',M+'/whisper'),
   ('yzd-v/DWPose','dw-ll_ucoco_384.pth',M+'/dwpose'),('ByteDance/LatentSync','latentsync_syncnet.pt',M+'/syncnet')]
for repo,f,d in G:
    p=hf_hub_download(repo,f,local_dir=d); print(p,os.path.getsize(p),flush=True)
subprocess.run(['curl','-sL','https://download.pytorch.org/models/resnet18-5c106cde.pth','-o',M+'/face-parse-bisent/resnet18-5c106cde.pth'],check=True)
out=M+'/face-parse-bisent/79999_iter.pth'
r=subprocess.run(['gdown','154JgKpzCPW82qINcVieuPH3fZ2e0P812','-O',out])
if not os.path.exists(out) or os.path.getsize(out)<1e6:
    for repo,f in [('ManyOtherFunctions/face-parse-bisent','79999_iter.pth'),('vivym/face-parsing-bisenet','79999_iter.pth'),('camenduru/MuseTalk','face-parse-bisent/79999_iter.pth')]:
        try:
            p=hf_hub_download(repo,f,local_dir='tmpfp'); os.replace(p,out); print('fallback',repo); break
        except Exception as e: print('fp fail',repo,str(e)[:100])
print('faceparse',os.path.exists(out) and os.path.getsize(out))
