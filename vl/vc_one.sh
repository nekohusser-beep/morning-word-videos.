#!/usr/bin/env bash
# voice-lab: convert ONE source clip ($CLIP, e.g. K_1) to the voice of vl/ref.wav with Seed-VC. Uploads V_<clip>.wav + a log.
set +e
mkdir -p src out
gh release download "$TAG" -p "${CLIP}.wav" -D src --clobber || { echo "no source $CLIP, skipping"; exit 0; }
git clone --depth 1 https://github.com/Plachtaa/seed-vc.git sv
( cd sv && pip install -q -r requirements.txt > ../log.txt 2>&1 )
cd sv
python inference.py --source "../src/${CLIP}.wav" --target ../vl/ref.wav --output ../out/tmp \
  --diffusion-steps 25 --length-adjust 1.0 --inference-cfg-rate 0.7 --f0-condition False --fp16 False >> ../log.txt 2>&1 \
  || echo FAILED >> ../log.txt
cd ..
g=$(ls out/tmp/*.wav 2>/dev/null | head -1)
[ -n "$g" ] && cp "$g" "V_${CLIP}.wav" && gh release upload "$TAG" "V_${CLIP}.wav" --clobber
tail -c 4000 log.txt > "vclog_${CLIP}.txt"
gh release upload "$TAG" "vclog_${CLIP}.txt" --clobber
exit 0
