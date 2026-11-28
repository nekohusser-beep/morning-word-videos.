# STARHEAD QC JOB (PICTURE ONLY): Psalms 1 to 150, visual version. Nov 28 2026, from Claude.
You are QC. Check cold against this spec. Answer PASS or FAIL with a reason per line (timestamp for every FAIL). You do not rebuild; a FAIL goes back to Claude. Neko gets the file only after your PASS, then he has the final say. NOTHING is posted until Neko says yes on this exact file.

## What this is (v2: smaller re-encode of the build you already passed; please re-confirm, see evidence.md)
- The same Psalms 1 to 150 sleep reading you already passed on Nov 28 (8:48:36, 1080p, 16:9, KJV, one narrator). Neko watched the plain version on his phone and said it plays but "it's just the reading, not a video", and asked for "Visuals".
- ONLY THE PICTURE CHANGED. The audio is the same stream: I compared the packet checksum of the audio in this file against the passed master and they match (MD5 46a3bd48e14ac0671c87b06d2039991a in both, see evidence.md). So your earlier audio verdicts (joins, spot clips, level, end tail) stand and are not re-asked here.
- New picture: the gold title card "The Book of Psalms / Psalms 1 to 150 . King James Version . for rest" for the first 54 s, a slow 12 s dissolve into scene 1, then 66 calm, dim, still scenes (night hills under a moon, still water with moon path, mist mountains, cedar ridges at dusk, dunes at dusk, Milky Way, dusk clouds, sunset sea, a lone tree at dusk, soft warm or cool bokeh lights, twilight pasture, dawn glow). Each holds about 7 min 45 s, then a 12 s dissolve to the next. The last scene holds to 8:47:36 and fades to black over the final 60 s.
- All pictures are drawn in code (free, no credits, no people, no animals, no text, no logos, no brands, no Bible book art). Dim on purpose for sleep: average brightness about 25 of 255.
- 1 frame per second (our sleep-reading standard); the file is H.264 High, 1080p, AAC-LC audio with a proper audio config (plays on phones; the earlier "can't play" problem was fixed in the plain version and the same method is used here).

## Files (all in this folder; review copies are 480p, the real master is the 455 MiB 1080p file (v2))
- contact-66-scenes.jpg: one frame from the middle of every scene, taken FROM the finished file. Left to right, top to bottom, 11 per row, 6 rows = scenes 1 to 66.
- scene-times.md: when each scene is fully on screen and when each dissolve runs.
- sample-start-0m-to-2m.mp4: first 2 minutes (title card, dissolve at 0:54 to 1:06 into scene 1, narrator starts the title and Psalm 1).
- sample-dissolve-A-scene10-to-11.mp4, B-scene33-to-34.mp4, C-scene50-to-51.mp4: 40 s each, the dissolve is in the middle (the dissolve runs from 14 s to 26 s inside each clip).
- sample-end-last-3m.mp4: last 3 minutes. The bed alone plays; the last scene holds to 2 minutes into the clip (31656 s) and fades to black over the final minute.
- proof.md and frames/: proof.py output on the finished file (5 frames), evidence.md (stream facts, audio checksum, whole-file brightness scan).

## What the machines already did (read evidence.md)
- Whole-file brightness scan of all 31,716 frames: after the title, every frame is between about 14 and 30 on a 0 to 255 scale; the biggest change from one frame to the next anywhere in the body is 1.4 levels (so no flash, no black dip, no cut). The only black is the deliberate fade at the very end.
- Frame count 31,716 = file length in seconds, 1 fps, audio and video the same length.

## Known flags in proof.md (expected, NOT defects unless you see or hear something)
- LOUDNESS about -18.2 LUFS (sleep-master level, same as the passed audio; proof.py expects -14 for a normal video).
- SILENT GAPS only after 31650 s (the bed fading below -50 dB by design).
- FRAMES 4 of 5: proof.py cannot grab the exact last second of a 1 fps file; the fifth frame is saved by hand.
- BLACK FRAMES: with the picture now lit all the way through, this check should read PASS honestly (the black at the very end is the planned fade).

## What PASS looks like
1. TITLE CARD (first 54 s): gold title readable at phone size, spelling right (The Book of Psalms / Psalms 1 to 150 . King James Version . for rest), no brand, no watermark.
2. FIRST DISSOLVE (0:54 to 1:06): the title fades into scene 1 smoothly. No black dip, no flash, no jump.
3. DISSOLVES A, B, C: each is a slow cross-dissolve between two calm scenes. No black dip, no flash, no hard cut, no stutter. (At 1 frame per second a 12 s dissolve is 12 steps; judge whether it still looks like a gentle fade.)
4. SCENES (contact sheet): calm and dim; nothing busy or startling; no text, no logo, no brand, no person, no animal, no readable symbol; no picture of the Bible with a steel square (it must not appear). Flag any scene you would change, by its position number.
5. END (last 3 minutes): last scene holds, then fades smoothly to black over the final minute; the file ends cleanly; the bed continues under it.
6. SLEEP FIT: dim enough and still enough to sleep to (no flashing, no fast movement, nothing bright except small stars and the moon).
7. AUDIO UNCHANGED: confirm the audio in the clips sounds the same as the passed master (voice, level, bed) and that nothing is out of sync with the picture at the start (narrator starts the title card line at the start of the file).

## Things only you can sign off on (reply PASS or FAIL on each)
A. TITLE CARD and FIRST DISSOLVE.  B. DISSOLVES A, B, C.  C. SCENES 1 to 66 (list any position numbers you would change).  D. END FADE.  E. SLEEP FIT (dim, still, calm).  F. AUDIO STILL THE SAME.

## Answer format
One line per item A to F plus a PASS/FAIL for the whole job. For each FAIL: the timestamp or scene number, what you saw, and what the fix should be. Then post the answer in this chat. If you cannot open a file, say which one; do not guess.
