#!/bin/bash
# ComfyUI + LTX-2.3 22B distilled (unsloth GGUF) text-to-video with audio, headless, free Kaggle T4. $0. Pin by commit SHA.
# License of the weights: LTX-2.x Community License (free commercial use under about $10M revenue), NOT Apache.
set -u
export PYTORCH_CUDA_ALLOC_CONF=${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}
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
start_server() {
  # fresh server each time when FRESH=1 (host RAM sits at 27-29 of 31 GB after one clip; a warm server was killed with the kernel)
  if [ "${1:-}" = "fresh" ]; then pkill -f "main.py --listen 127.0.0.1 --port 8188" 2>/dev/null; sleep 6; fi
  if ! curl -s http://127.0.0.1:8188/system_stats >/dev/null; then
    log "start server"; ( cd ComfyUI && nohup python main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch ${COMFY_ARGS:-} > ../comfy.log 2>&1 < /dev/null & )
    for i in $(seq 1 120); do curl -s http://127.0.0.1:8188/system_stats >/dev/null && break; sleep 2; done
  fi
}
if [ -n "${SCENES:-}" ]; then start_server fresh; else start_server; fi
curl -s http://127.0.0.1:8188/system_stats | head -c 500; echo
grep -i -E "error|Traceback|import failed|IMPORT FAILED" comfy.log | head -10
rm -f mem.log
( while true; do echo "$(( $(date +%s) - T0 ))s $(nvidia-smi --query-gpu=memory.used --format=csv,noheader | tr '\n' ' ') RAM_used_GB=$(free -g | awk 'NR==2{print $3}')" >> mem.log; sleep 20; done ) &
MEMPID=$!
if [ -n "${SCENES:-}" ]; then
  # SCENES=<file in tests/kaggle-ltx> with one "name|prompt" per line: one clip per line, time + peak memory logged per clip.
  curl -sfL "$RAW/$SCENES" -o scenes.txt || { log "FAIL fetch $SCENES"; kill $MEMPID; exit 1; }
  CSV=/kaggle/working/ltx_timings${TAG:-}.csv
  echo "scene,total_wall_s,final_attempt_gen_s,attempts,peak_gpu0_mib_sampled_20s,peak_ram_gb" > "$CSV"
  i=0
  UN=$(cat unet_name.txt); GE=$(cat gemma_name.txt)
  # WARM-UP: the first clip on any fresh server OOMs in the sampler (Gemma text encoder still sits on the GPU when the 13 GB UNet loads); a retry on
  # the same server succeeds because the text encoding is cached and only the UNet has to fit. So encode this scene's prompt first with a tiny latent
  # (256x256, 9 frames), then the real run finds the encoding cached. A failed warm-up is not fatal.
  warm() {
    PROMPT="$1" SEED=1 WID=256 HGT=256 LEN=9 UNET="$UN" GEMMA="$GE" python wf_ltx.py "ltx/warm_$2" </dev/null > /tmp/warm.out 2>&1 \
      && log "warm-up ok $2 ($(grep -o 'WALL_SECONDS [0-9.]*' /tmp/warm.out))" || { log "warm-up failed $2"; tail -3 /tmp/warm.out; }
    rm -rf ComfyUI/output/ltx/warm_* ComfyUI/output/audio/ltx/warm_* 2>/dev/null
  }
  # fd 3 for the scene list: ffmpeg/python inside the loop must not eat it (a stdin read swallowed scenes 4-5 on the first run)
  while IFS='|' read -r NAME PROMPT <&3; do
    [ -z "$NAME" ] && continue; i=$((i + 1)); S0=$(date +%s); log "SCENE $i $NAME start"
    # host RAM sits near the 31 GB kill line after a clip: between scenes restart the server if more than 22 GB is in use
    USED=$(free -g | awk 'NR==2{print $3}'); [ "$USED" -gt 22 ] && { log "RAM ${USED} GB used, restarting server between scenes"; start_server fresh; }
    warm "$PROMPT" "$NAME"
    OK=0; GEN=""
    for ATT in 1 2 3; do
      [ "$ATT" = "3" ] && { log "attempt 3: fresh server + warm-up"; start_server fresh; warm "$PROMPT" "$NAME"; }
      PROMPT="$PROMPT" SEED=$((${SEEDBASE:-20261200} + i)) UNET="$UN" GEMMA="$GE" python wf_ltx.py "ltx/$NAME" </dev/null 2>&1 | tee /tmp/main.out | grep -v '^\.\.\.running'
      if [ "${PIPESTATUS[0]}" = "0" ]; then OK=1; GEN=$(grep -o 'WALL_SECONDS [0-9.]*' /tmp/main.out | awk '{print $2}'); break; fi
      log "SCENE $NAME attempt $ATT FAILED"; tail -120 comfy.log > "/kaggle/working/ltx_fail_${NAME}_a${ATT}.log"; grep -E "OOM|out of memory|Allocation|Tried to allocate" comfy.log | tail -3
    done
    [ "$OK" = "1" ] || { log "SCENE $NAME GAVE UP"; echo "$NAME,FAILED,,$ATT,," >> "$CSV"; continue; }
    S1=$(date +%s)
    PEAKS=$(python - "$((S0 - T0))" "$((S1 - T0))" <<'PY'
import re, sys
a, b = int(sys.argv[1]), int(sys.argv[2]); g = r = 0
for l in open("mem.log"):
    m = re.match(r"(\d+)s (\d+) MiB .*RAM_used_GB=(\d+)", l)
    if m and a <= int(m.group(1)) <= b: g = max(g, int(m.group(2))); r = max(r, int(m.group(3)))
print(f"{g},{r}")
PY
)
    NAME="$NAME" NOPUSH=1 python post_ltx.py ComfyUI/output "ltx/$NAME" /kaggle/working </dev/null || log "POST FAILED $NAME"
    echo "$NAME,$((S1 - S0)),$GEN,$ATT,$PEAKS" >> "$CSV"
    log "SCENE $NAME done: $((S1 - S0)) s total, $GEN s final generation, attempt $ATT, peaks gpu0,ram = $PEAKS"
  done 3< scenes.txt
  kill $MEMPID; echo "TIMINGS"; cat "$CSV"; cp mem.log "/kaggle/working/ltx_mem${TAG:-}.log"; log "DONE scenes"; exit 0
fi
log "run workflow ${WID:-480}x${HGT:-832} len=${LEN:-97}"
UNET=$(cat unet_name.txt) GEMMA=$(cat gemma_name.txt) python wf_ltx.py ltx/verse || { log "WORKFLOW FAILED"; tail -80 comfy.log; kill $MEMPID; tail -15 mem.log; exit 2; }
kill $MEMPID; echo "MEM LOG (peak lines)"; sort -t= -k1 mem.log | tail -3; tail -3 mem.log
grep -E "Prompt executed|out of memory|OOM|lowvram|offload" comfy.log | tail -6
log "post"
python post_ltx.py ComfyUI/output ltx/verse /kaggle/working || log "POST FAILED"
log "DONE"
