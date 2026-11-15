#!/bin/bash
# ComfyUI + Wan 2.2 5B image-to-video, headless, on a free Kaggle T4. $0. Pin this script by commit SHA when fetching.
set -u
SHA=${SHA:-main}
RAW=https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./$SHA/tests/kaggle-comfyui
W=${W:-/kaggle/temp/comfy}; mkdir -p "$W" /kaggle/working 2>/dev/null || { W=/tmp/comfy; mkdir -p "$W"; }
cd "$W"; T0=$(date +%s)
log() { echo "[$(( $(date +%s) - T0 ))s] $*"; }
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; df -h "$W" | tail -1; free -g | sed -n 2p
for f in wf.py post.py skip_fridge.jpg; do curl -sfL "$RAW/$f" -o "$f" || { log "FAIL fetch $f"; exit 1; }; done
if [ ! -d ComfyUI ]; then log "clone ComfyUI"; git clone -q --depth 1 https://github.com/comfyanonymous/ComfyUI || exit 1; fi
( cd ComfyUI && git log -1 --format='COMFYUI_COMMIT %h %cd' --date=short )
log "pip install requirements (torch stays as Kaggle has it)"
pip install -q -r ComfyUI/requirements.txt 2>&1 | tail -3
python - <<'PY'
import torch; print("TORCH", torch.__version__, "CUDA", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")
PY
log "models"
python - <<'PY'
import os, shutil
from huggingface_hub import hf_hub_download, list_repo_files
repo = "Comfy-Org/Wan_2.2_ComfyUI_Repackaged"
files = list_repo_files(repo)
want = {"diffusion_models": "wan2.2_ti2v_5B_fp16.safetensors", "text_encoders": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "vae": "wan2.2_vae.safetensors"}
for sub, name in want.items():
    dst = f"ComfyUI/models/{sub}/{name}"
    if os.path.exists(dst): print("HAVE", dst); continue
    m = [f for f in files if f.endswith("/" + name)]
    print("REPO MATCH", name, m)
    if not m: print("MISSING in repo, candidates:", [f for f in files if "5B" in f or "umt5" in f or "vae" in f][:20]); raise SystemExit(4)
    p = hf_hub_download(repo, m[0], local_dir="dl")
    os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.move(p, dst); print("GOT", dst, os.path.getsize(dst) // 1048576, "MB")
PY
[ $? -eq 0 ] || { log "FAIL models"; exit 1; }
cp skip_fridge.jpg ComfyUI/input/
if ! curl -s http://127.0.0.1:8188/system_stats >/dev/null; then
  log "start server"; ( cd ComfyUI && nohup python main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch > ../comfy.log 2>&1 & )
  for i in $(seq 1 90); do curl -s http://127.0.0.1:8188/system_stats >/dev/null && break; sleep 2; done
fi
curl -s http://127.0.0.1:8188/system_stats | head -c 400; echo
LEN=${LEN:-73}; WID=${WID:-480}; HGT=${HGT:-832}
log "run workflow length=$LEN ${WID}x${HGT}"
python wf.py skip_fridge.jpg wan5b/skip "$LEN" "$WID" "$HGT" 20261115 || { log "WORKFLOW FAILED"; tail -60 comfy.log; exit 2; }
grep -E "Prompt executed|Requested to load|out of memory|OOM|tiled" comfy.log | tail -8
log "post"
python post.py ComfyUI/output/wan5b skip skip_fridge.jpg /kaggle/working || { log "POST FAILED"; tail -30 comfy.log; exit 3; }
log "DONE"
