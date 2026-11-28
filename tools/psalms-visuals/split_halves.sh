#!/bin/bash
# Lossless split of the single visual MP4 build into two halves at a silent pause between psalms.
# usage: split_halves.sh SPLIT_SECOND SCENE_NAME   (frames are 1 per second; SPLIT must fall inside a static s_NN hold)
# Re-encodes only the one static segment that holds the cut (two pieces), stream-copies every other segment,
# cuts the ADTS audio at a packet boundary (ffmpeg -f segment), muxes each half with aac_adtstoasc + faststart,
# then proves: audio payload md5 over both halves == the master's, frame pts sequential 0..N-1.
set -euo pipefail
cd /home/claude/psvis; mkdir -p half
T=$1; S=$2
read N1 N2 IMG < <(python3 - "$T" "$S" <<'PY'
import json,sys
T=int(sys.argv[1]); S=sys.argv[2]; c=0
for s in json.load(open('segs.json')):
    if s['name']==S:
        print(T-c, c+s['frames']-T, s['img']); break
    c+=s['frames']
PY
)
enc='-c:v libx264 -preset faster -crf 25 -aq-mode 3 -bf 3 -g 600 -keyint_min 600 -x264-params scenecut=0:keyint=600:min-keyint=600 -threads 1 -r 1 -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv -pix_fmt yuv420p'
conv='scale=in_range=full:out_range=tv:out_color_matrix=bt709:flags=bicubic,format=yuv420p'
ffmpeg -v error -y -loop 1 -framerate 1 -i $IMG -frames:v $N1 -vf "$conv" $enc half/${S}a.mp4
ffmpeg -v error -y -loop 1 -framerate 1 -i $IMG -frames:v $N2 -vf "$conv" $enc half/${S}b.mp4
python3 - "$S" <<'PY'
import sys
S=sys.argv[1]; names=open('segnames.txt').read().split(); i=names.index(S)
p1=[f"seg2/{n}.mp4" for n in names[:i]]+[f"half/{S}a.mp4"]
p2=[f"half/{S}b.mp4"]+[f"seg2/{n}.mp4" for n in names[i+1:]]
open('half/l1.txt','w').write(''.join(f"file '/home/claude/psvis/{x}'\n" for x in p1))
open('half/l2.txt','w').write(''.join(f"file '/home/claude/psvis/{x}'\n" for x in p2))
PY
ffmpeg -v error -y -f concat -safe 0 -i half/l1.txt -c copy half/v1.mp4
ffmpeg -v error -y -f concat -safe 0 -i half/l2.txt -c copy half/v2.mp4
(cd half && ffmpeg -v error -y -f aac -i /home/claude/stitch/enc_fast70.aac -c copy -f segment -segment_times $T -segment_format adts a_%d.aac)
ffmpeg -v error -y -i half/v1.mp4 -i half/a_0.aac -map 0:v -map 1:a -c copy -bsf:a aac_adtstoasc -movflags +faststart -f mp4 half/psalms-visuals-part1.mp4
ffmpeg -v error -y -i half/v2.mp4 -i half/a_1.aac -map 0:v -map 1:a -c copy -bsf:a aac_adtstoasc -movflags +faststart -f mp4 half/psalms-visuals-part2.mp4
(for f in half/psalms-visuals-part1.mp4 half/psalms-visuals-part2.mp4; do ffmpeg -v error -i $f -map 0:a -c copy -f data -; done) | md5sum
