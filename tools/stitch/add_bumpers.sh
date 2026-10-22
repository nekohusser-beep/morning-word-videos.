#!/bin/bash
# usage: add_bumpers.sh in.mp4 out.mp4  -> Day 1 opening song card + video + closing song card
set -e
D="$(dirname "$0")/bumpers"
ffmpeg -v error -y -i "$D/intro.mp4" -i "$1" -i "$D/outro.mp4" -filter_complex \
"[0:v]fps=30,scale=720:1280,setsar=1[v0];[1:v]fps=30,scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1[v1];[2:v]fps=30,scale=720:1280,setsar=1[v2];\
[0:a]aresample=48000,aformat=channel_layouts=stereo[a0];[1:a]aresample=48000,aformat=channel_layouts=stereo[a1];[2:a]aresample=48000,aformat=channel_layouts=stereo[a2];\
[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k "$2"
