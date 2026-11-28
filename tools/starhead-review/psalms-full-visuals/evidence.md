# evidence.md (visual version v2, the smaller re-encode, built Nov 28 2026 8:06 AM ET)

## Why there is a second build
The first build (psalms-visuals-v1.mp4, 523.4 MiB) is what you passed. It is over the 500 MiB chat limit, so Neko could not receive it. v2 is the SAME scenes, SAME timeline, SAME audio, with the picture re-encoded smaller (B-frames and longer keyframe interval, no look change): 476,546,293 bytes = 454.5 MiB. Please re-confirm that the picture still passes. Nothing else changed.

## File
H.264 High 1920x1080, 1 fps, 31,716 frames, 31,716.000 s; AAC-LC mono 48 kHz with audio config present (extradata 2 bytes), faststart. Frame times are exactly 0,1,2,...,31715 s (checked on all 31,716 packets), so there is no drift between picture and audio.

## Audio is unchanged (packet checksum, copy mode)
v2 : MD5=46a3bd48e14ac0671c87b06d2039991a
v1 (what you passed) and the Starhead-passed master: MD5=46a3bd48e14ac0671c87b06d2039991a

## Picture is unchanged (v1 against v2)
Mean absolute pixel difference at one frame from the middle of each of the 66 scenes: 0.12 of 255 on average (largest 0.15). Whole-file brightness scan, all 31,716 frames, largest difference in a frame's average brightness between v1 and v2: 0.16 of 255.

## Brightness scan of v2, all 31,716 frames (luma 0 to 255)
title (0-50 s) mean 11.3; body (70 s to 31646 s): min 13.9, max 30.5, mean 24.8; largest frame-to-frame step in the body 1.34, anywhere 1.63 (inside the first dissolve); fade: 31656 s = 25.4, 31686 s = 12.9, last frame = 0.8.
