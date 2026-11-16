#!/bin/bash
# usage: scene.sh N TARGET_SECONDS PINGPONG(1/0)
N=$1; T=$2; PP=$3
IN=/tmp/nw/c/s$N.mp4; OUT=/tmp/nw/s/s$N.mp4
if [ "$PP" = "1" ]; then BASE=8.0; PRE="[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0[pp]"; else BASE=4.0; PRE="[0:v]null[pp]"; fi
F=$(python3 -c "print(max(1.0,$T/$BASE))")
ffmpeg -y -v error -i $IN -an -filter_complex "$PRE;[pp]setpts=$F*PTS,minterpolate=fps=24:mi_mode=mci:mc_mode=obmc:me_mode=bidir:vsbmc=1,trim=duration=$T,setpts=PTS-STARTPTS,scale=1080:1920:flags=lanczos,unsharp=5:5:0.6:5:5:0,eq=contrast=1.04:saturation=1.05,vignette=PI/5,noise=alls=5:allf=t,format=yuv420p[v]" -map "[v]" -r 24 -c:v libx264 -preset veryfast -crf 14 $OUT && echo "scene $N F=$F ok" 
