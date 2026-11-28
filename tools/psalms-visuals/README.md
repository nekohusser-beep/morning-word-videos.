# Psalms 1-150 visual build (Nov 28 2026)

Slow dim procedural scenes under the untouched Psalms 1-150 sleep-reading audio (8:48:36, 1 fps, 1080p).
Nothing here is Scripture text or a face: 66 abstract night/dawn/water/mist/cedar/dune/sky scenes drawn in code.

- gen_scenes.py: draws the 66 scene PNGs (`python3 gen_scenes.py OUTDIR [indices]`).
- plan.py: timeline -> segs.json (title hold 54 s, 12 s dissolves, 66 holds of ~479 s, 60 s fade to black, 31716 frames).
- mkseg.sh NAME: encodes one segment (x264 -bf 3 -g 600 scenecut=0: a static scene costs ~0.8 MB instead of ~1.8 MB).
- finish_build.sh: concat the segments, mux with the ADTS audio master (aac_adtstoasc, faststart).
- split_halves.sh SECOND SEG: lossless two-halves split when chat refuses one big file (see lessons).

Delivery checks: ffprobe audio profile=LC and extradata_size=2; audio payload md5 identical to the master;
frame pts sequential; file under ~400 MiB per chat upload.
