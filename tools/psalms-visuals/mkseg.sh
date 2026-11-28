#!/bin/bash
# usage: mkseg.sh NAME  (reads segs.json)
cd /home/claude/psvis
NAME=$1
python3 - "$NAME" <<'PY' > /tmp/cmd_$NAME.sh
import json, sys
n = sys.argv[1]
s = [x for x in json.load(open('segs.json')) if x['name'] == n][0]
F = s['frames']
enc = ('-c:v libx264 -preset faster -crf 25 -aq-mode 3 -bf 3 -g 600 -keyint_min 600 '
       '-x264-params scenecut=0:keyint=600:min-keyint=600 -threads 1 -r 1 '
       '-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv -pix_fmt yuv420p')
conv = 'scale=in_range=full:out_range=tv:out_color_matrix=bt709:flags=bicubic,format=yuv420p'
out = f'seg2/{n}.mp4'
if s['kind'] == 'static':
    print(f"ffmpeg -v error -y -loop 1 -framerate 1 -i {s['img']} -frames:v {F} -vf \"{conv}\" {enc} {out}")
elif s['kind'] == 'xfade':
    print(f"ffmpeg -v error -y -loop 1 -framerate 1 -t 12 -i {s['a']} -loop 1 -framerate 1 -t 12 -i {s['b']} "
          f"-filter_complex \"[0:v][1:v]xfade=transition=fade:duration=12:offset=0,{conv}\" -frames:v {F} {enc} {out}")
else:
    print(f"ffmpeg -v error -y -loop 1 -framerate 1 -i {s['img']} -frames:v {F} -vf \"fade=t=out:st=0:d=60,{conv}\" {enc} {out}")
PY
bash /tmp/cmd_$NAME.sh && echo "done $NAME"
