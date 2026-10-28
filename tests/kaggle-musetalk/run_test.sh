#!/bin/bash
# $0 test: MuseTalk 1.5 lip-sync on Kaggle's free GPU, Kokoro voice, Whisper word check, loudness and size check.
# Re-run safe: finished stages are skipped. Run from a Kaggle notebook (GPU on, Internet on).
set -u
W=/kaggle/working
RAW=https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./main/tests/kaggle-musetalk
mkdir -p $W/t && cd $W/t
log(){ echo "== $(date +%H:%M:%S) $*"; }
fail(){ echo "!! FAILED: $1"; [ -n "${2:-}" ] && [ -f "$2" ] && tail -n 45 "$2"; exit 1; }

log "STAGE 0 environment"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
python3 --version
which ffmpeg >/dev/null || { apt-get install -y -qq ffmpeg >/dev/null 2>&1; }
which ffmpeg
df -h $W | tail -1
curl -s -m 10 -o /dev/null -w "github %{http_code}\n" https://github.com
curl -s -m 10 -o /dev/null -w "huggingface %{http_code}\n" https://huggingface.co
for f in script.txt tts.py check.py dl_weights.py grid.py derrick-base-5s.mp4 derrick-still-5s.mp4; do
  curl -sfL -o $f $RAW/$f || fail "download $f"
done

if [ ! -f voice.wav ]; then
  log "STAGE 1 Kokoro voice (Python 3.11 venv, CPU)"
  apt-get install -y -qq espeak-ng >/dev/null 2>&1
  pip install -q uv > s1.log 2>&1 || fail "pip uv" s1.log
  uv venv --python 3.11 ttsenv >> s1.log 2>&1 || fail "uv venv 3.11" s1.log
  TT="uv pip install --python $W/t/ttsenv/bin/python"
  $TT torch --index-url https://download.pytorch.org/whl/cpu >> s1.log 2>&1 || fail "torch cpu" s1.log
  $TT pip "numpy<2" kokoro soundfile faster-whisper >> s1.log 2>&1 || fail "kokoro install" s1.log
  $TT "en_core_web_sm@https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl" >> s1.log 2>&1 || echo "spacy model wheel failed (kokoro may fetch it itself)"
  $W/t/ttsenv/bin/python tts.py am_michael 0.92 > tts.log 2>&1 || fail "tts" tts.log
fi
grep VOICE_SECONDS tts.log

MT="uv pip install --python $W/t/mtenv/bin/python"
if [ ! -f .s2 ]; then
  log "STAGE 2 MuseTalk env: Python 3.10, torch 2.0.1 cu118, mmcv 2.0.1"
  pip install -q uv > s2.log 2>&1 || fail "pip uv" s2.log
  uv venv --python 3.10 mtenv >> s2.log 2>&1 || fail "uv venv 3.10" s2.log
  $MT torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118 >> s2.log 2>&1 || fail "torch 2.0.1" s2.log
  $MT numpy==1.23.5 diffusers==0.30.2 accelerate==0.28.0 opencv-python==4.9.0.80 soundfile==0.12.1 transformers==4.39.2 huggingface_hub==0.30.2 librosa==0.11.0 einops==0.8.1 omegaconf ffmpeg-python moviepy gdown requests "imageio[ffmpeg]" scipy matplotlib tqdm pyyaml >> s2.log 2>&1 || fail "musetalk requirements" s2.log
  $MT mmengine >> s2.log 2>&1 || fail "mmengine" s2.log
  $MT "mmcv==2.0.1" --no-build -f https://download.openmmlab.com/mmcv/dist/cu118/torch2.0.0/index.html >> s2.log 2>&1 || fail "mmcv wheel" s2.log
  $MT "mmdet==3.1.0" --no-deps >> s2.log 2>&1 && $MT pycocotools shapely six terminaltables >> s2.log 2>&1 || fail "mmdet" s2.log
  $MT "mmpose==1.1.0" --no-deps >> s2.log 2>&1 && $MT json_tricks munkres xtcocotools >> s2.log 2>&1 || fail "mmpose" s2.log
  touch .s2
fi

if [ ! -f .s3 ]; then
  log "STAGE 3 MuseTalk code and weights"
  [ -d MuseTalk ] || git clone -q --depth 1 https://github.com/TMElyralab/MuseTalk.git > s3.log 2>&1 || fail "git clone" s3.log
  cd MuseTalk
  cp ../dl_weights.py .
  $W/t/mtenv/bin/python dl_weights.py >> ../s3.log 2>&1 || fail "weights" ../s3.log
  cd ..
  touch .s3
fi

run_arm(){
  arm=$1
  cat > cfg_$arm.yaml <<EOC
task_0:
 video_path: "$W/t/derrick-$arm-5s.mp4"
 audio_path: "$W/t/voice.wav"
EOC
  log "STAGE 4 lip-sync: $arm"
  ( cd MuseTalk && s=$(date +%s.%N) && $W/t/mtenv/bin/python -m scripts.inference --inference_config ../cfg_$arm.yaml --result_dir ../results_$arm --unet_model_path models/musetalkV15/unet.pth --unet_config models/musetalkV15/musetalk.json --version v15 --use_float16 > ../infer_$arm.log 2>&1; rc=$?; e=$(date +%s.%N); echo "$rc $(echo "$e - $s" | bc)" > ../time_$arm.txt )
  read rc secs < time_$arm.txt
  if [ "$rc" != "0" ]; then fail "inference $arm (exit $rc)" infer_$arm.log; fi
  echo "MUSETALK_WALL_SECONDS $arm $secs"
}
[ -f time_base.txt ] && [ "$(cut -d' ' -f1 time_base.txt)" = "0" ] || run_arm base
[ -f time_still.txt ] && [ "$(cut -d' ' -f1 time_still.txt)" = "0" ] || run_arm still

log "STAGE 5 finish: loudness, size, word check, frames"
mkdir -p out
for arm in base still; do
  f=$(find results_$arm -name '*.mp4' ! -name 'temp*' | head -1)
  [ -n "$f" ] || fail "no output mp4 for $arm" infer_$arm.log
  ffmpeg -y -loglevel error -i "$f" -af "loudnorm=I=-14:TP=-1.5:LRA=11" -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.5:5:5:0.0" -c:v libx264 -crf 17 -preset veryfast -pix_fmt yuv420p -c:a aac -b:a 192k out/final_$arm.mp4 || fail "ffmpeg final $arm"
  ffmpeg -y -loglevel error -i out/final_$arm.mp4 -vf scale=360:640 -c:v libx264 -crf 30 -preset veryfast -c:a aac -b:a 96k out/small_$arm.mp4
  echo "--- loudness $arm"
  ffmpeg -nostats -i out/final_$arm.mp4 -filter_complex ebur128=peak=true -f null - 2>&1 | tail -n 14 | grep -E "I:|Peak:"
  ffprobe -v error -show_entries stream=codec_type,width,height,r_frame_rate,duration -of csv=p=0 out/final_$arm.mp4 | tr '\n' ' '; echo
done
$W/t/ttsenv/bin/python check.py out/final_base.mp4 out/final_still.mp4 | grep -E "^CHECK"
# frames: full and mouth zoom at three times
for arm in base still; do
  if [ $arm = base ]; then CX=322; CY=816; else CX=322; CY=547; fi
  for t in 2 7 12; do
    ffmpeg -y -loglevel error -ss $t -i out/final_$arm.mp4 -frames:v 1 -vf "scale=360:-1" out/f_${arm}_$t.png
    ffmpeg -y -loglevel error -ss $t -i out/final_$arm.mp4 -frames:v 1 -vf "crop=480:360:$CX:$CY,scale=360:-1" out/z_${arm}_$t.png
  done
done
python3 grid.py
cp voice.wav out/voice.wav
log "DONE"
echo "REAL_TIME_FACTOR base: $(cut -d' ' -f2 time_base.txt) s wall for $(grep -o 'VOICE_SECONDS [0-9.]*' tts.log | cut -d' ' -f2) s of audio (includes model load)"
echo "REAL_TIME_FACTOR still: $(cut -d' ' -f2 time_still.txt) s wall"
