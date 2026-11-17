#!/bin/bash
# mux.sh <line NN> <source clip mp4> <vc wav> [stretch factor]
# Puts the Seed-VC voice back onto the Veo clip's own picture (same timing), writes clips/cNN.mp4.
# Optional stretch factor >1 slows picture and voice together (never a speed-up).
set -e
N=$(printf %02d "$1"); SRC="$2"; VC="$3"; F="${4:-1}"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$SRC")
if [ "$F" = "1" ]; then
  ffmpeg -v error -y -i "$SRC" -i "$VC" -map 0:v:0 -map 1:a:0 -af "apad" -t "$D" -c:v copy -c:a aac -b:a 256k -ar 48000 "clips/c$N.mp4"
else
  AT=$(python3 -c "print(1/$F)")
  ffmpeg -v error -y -i "$SRC" -i "$VC" -map 0:v:0 -map 1:a:0 -vf "setpts=$F*PTS" -af "apad,atempo=$AT" -t "$(python3 -c "print($D*$F)")" -r 30 -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p -c:a aac -b:a 256k -ar 48000 "clips/c$N.mp4"
fi
echo "c$N <- $(basename $SRC) + $(basename $VC) stretch $F  dur $(ffprobe -v error -show_entries format=duration -of csv=p=0 clips/c$N.mp4)"
