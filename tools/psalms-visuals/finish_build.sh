#!/bin/bash
set -e
cd /home/claude/psvis
for n in $(cat segnames.txt); do [ -s seg2/$n.mp4 ] || { echo "MISSING $n"; exit 1; }; echo "file 'seg2/$n.mp4'"; done > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy -movflags +faststart vtrack.mp4
echo "vtrack: $(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames,r_frame_rate,avg_frame_rate -of csv=p=0 vtrack.mp4) $(ffprobe -v error -show_entries format=duration -of csv=p=0 vtrack.mp4)"
ffmpeg -v error -y -i vtrack.mp4 -i /home/claude/stitch/enc_fast70.aac -map 0:v -map 1:a -c copy -bsf:a aac_adtstoasc -movflags +faststart -f mp4 psalms-visuals-v2.mp4
ls -la psalms-visuals-v2.mp4
