#!/bin/bash
# ComfyUI + LTX-2.3 22B distilled (unsloth GGUF) text-to-video with audio, headless, free Kaggle T4. $0. Pin by commit SHA.
# License of the weights: LTX-2.x Community License (free commercial use under about $10M revenue), NOT Apache.
set -u
SHA=${SHA:-main}
RAW=https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./$SHA/tests/kaggle-ltx
W=${W:-/kaggle/temp/ltx}; mkdir -p "$W" /kaggle/working 2>/dev/null || { W=/tmp/ltx; mkdir -p "$W"; }
cd "$W"; T0=$(date +%s)
log() { echo "[$(( $(date +%s) - T0 ))s] $*"; }
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; df -h "$W" | tail -1; free -g | sed -n 2p
for f in wf_ltx.py post_ltx.py; do curl -sfL "$RAW/$f" -o "$f" || { log "FAIL fetch $f"; exit 1; }; done
if [ ! -d ComfyUI ]; then log "clone ComfyUI"; git clone -q --depth 1 https://github.com/Comfy-Org/ComfyUI || exit 1; fi
if [ ! -d ComfyUI/custom_nodes/ComfyUI-GGUF ]; then git clone -q --depth 1 https://github.com/city96/ComfyUI-GGUF ComfyUI/custom_nodes/ComfyUI-GGUF || exit 1; fi
( cd ComfyUI && git log -1 --format='COMFYUI_COMMIT %h %cd' --date=short ); ( cd ComfyUI/custom_nodes/ComfyUI-GGUF && git log -1 --format='GGUF_COMMIT %h %cd' --date=short )
log "pip install (torch stays as Kaggle has it)"
pip install -q -r ComfyUI/requirements.txt 2>&1 | tail -3
pip install -q gguf sentencepiece protobuf 2>&1 | tail -3
python - <<'PY'
import torch; print("TORCH", torch.__version__, "CUDA", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")
PY
log "models"
QUANT=${QUANT:-distilled/ltx-2.3-22b-distilled-Q4_K_S.gguf} python - <<'PY'
import os, shutil
from huggingface_hub import hf_hub_download, list_repo_files
M = "ComfyUI/models"
def get(repo, rel, sub):
    dst = f"{M}/{sub}/{os.path.basename(rel)}"
    if os.path.exists(dst): print("HAVE", dst); return dst
    files = list_repo_files(repo)
    if rel not in files:
        print("MISSING", repo, rel, "candidates:", [f for f in files if f.endswith(('.gguf', '.safetensors'))][:60]); raise SystemExit(4)
    p = hf_hub_download(repo, rel, local_dir="dl")
    os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.move(p, dst)
    print("GOT", dst, os.path.getsize(dst) // 1048576, "MB", flush=True); return dst
R = "unsloth/LTX-2.3-GGUF"
get(R, os.environ["QUANT"], "unet")
get(R, "text_encoders/ltx-2.3-22b-distilled_embeddings_connectors.safetensors", "text_encoders")
get(R, "vae/ltx-2.3-22b-distilled_video_vae.safetensors", "vae")
get(R, "vae/ltx-2.3-22b-distilled_audio_vae.safetensors", "checkpoints")
G = "unsloth/gemma-3-12b-it-qat-GGUF"
gf = list_repo_files(G)
pick = [f for f in gf if "UD-Q4_K_XL" in f and f.endswith(".gguf") and "mmproj" not in f] or [f for f in gf if "Q4_K_M" in f and f.endswith(".gguf") and "mmproj" not in f]
print("GEMMA PICK", pick, "ALL", [f for f in gf if f.endswith(".gguf")])
if not pick: raise SystemExit(4)
get(G, pick[0], "text_encoders")
if "mmproj-BF16.gguf" in gf: get(G, "mmproj-BF16.gguf", "text_encoders")
open("gemma_name.txt", "w").write(os.path.basename(pick[0]))
open("unet_name.txt", "w").write(os.path.basename(os.environ["QUANT"]))
PY
[ $? -eq 0 ] || { log "FAIL models"; exit 1; }
df -h "$W" | tail -1
if ! curl -s http://127.0.0.1:8188/system_stats >/dev/null; then
  log "start server"; ( cd ComfyUI && nohup python main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch ${COMFY_ARGS:-} > ../comfy.log 2>&1 & )
  for i in $(seq 1 120); do curl -s http://127.0.0.1:8188/system_stats >/dev/null && break; sleep 2; done
fi
curl -s http://127.0.0.1:8188/system_stats | head -c 500; echo
grep -i -E "error|Traceback|import failed|IMPORT FAILED" comfy.log | head -10
( while true; do echo "$(( $(date +%s) - T0 ))s $(nvidia-smi --query-gpu=memory.used --format=csv,noheader | tr '\n' ' ') RAM_used_GB=$(free -g | awk 'NR==2{print $3}')" >> mem.log; sleep 20; done ) &
MEMPID=$!
log "run workflow ${WID:-480}x${HGT:-832} len=${LEN:-97}"
UNET=$(cat unet_name.txt) GEMMA=$(cat gemma_name.txt) python wf_ltx.py ltx/verse || { log "WORKFLOW FAILED"; tail -80 comfy.log; kill $MEMPID; tail -15 mem.log; exit 2; }
kill $MEMPID; echo "MEM LOG (peak lines)"; sort -t= -k1 mem.log | tail -3; tail -3 mem.log
grep -E "Prompt executed|out of memory|OOM|lowvram|offload" comfy.log | tail -6
log "post"
python post_ltx.py ComfyUI/output ltx/verse /kaggle/working || log "POST FAILED"
log "DONE"
