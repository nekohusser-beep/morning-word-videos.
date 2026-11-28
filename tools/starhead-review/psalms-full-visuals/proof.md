# PROOF PACK for psalms-visuals-v1.mp4
built Nov 28 2026 07:39 AM ET | sha256 79139aace3690a6b... | 548876505 bytes

| # | Check | Result |
|---|---|---|
| 1 | FILE (has video and audio, landscape, longer than 1s) | **PASS** |
| 2 | LOUDNESS (-14 LUFS +/-2, true peak at or under -1 dB) | **FAIL** |
| 3 | BLACK FRAMES (none in the middle of the video) | **FAIL** |
| 4 | SILENT GAPS (no full-mix silence of 1 s or more) | **FAIL** |
| 5 | FRAMES (first, quarter, middle, three-quarter, last saved for the reviewer to LOOK at) | **FAIL** |
| 6 | BANNED PHRASES (tools/humanize/gate.py on the script) | **PASS** |
| 7 | WORDS PER LINE | **PASS** |
| 8 | HEARD vs WRITTEN (strict word-for-word) | **PASS** |
| 9 | SCRIPTURE on screen vs KJV source (Psalms 1-150 (title line only; the Psalms are audio, see verse-check)) | **PASS** |
| 10 | SCRIPTURE spoken vs KJV source (Psalms 1-150 (title line only; the Psalms are audio, see verse-check)) | **PASS** |

## Raw evidence
### 1. FILE (has video and audio, landscape, longer than 1s): PASS
```
duration 31716.00s | video h264 1920x1080 | audio aac 48000 Hz
```
### 2. LOUDNESS (-14 LUFS +/-2, true peak at or under -1 dB): FAIL
```
integrated -18.24 LUFS | true peak -1.33 dBTP | LRA 5.70
```
### 3. BLACK FRAMES (none in the middle of the video): FAIL
```
black at 31696.00-31715.00s
```
### 4. SILENT GAPS (no full-mix silence of 1 s or more): FAIL
```
silence at 31650.50-31651.60s; 31655.90-31659.50s; 31659.50-31661.10s; 31661.10-31663.80s; 31663.80-31668.50s
```
### 5. FRAMES (first, quarter, middle, three-quarter, last saved for the reviewer to LOOK at): FAIL
```
4/5 frames in /home/claude/psvis/proof/frames; contact sheet /home/claude/psvis/proof/contact.png. Face, outfit, set, text, banned picture: reviewer eyes, not a script.
```
### 6. BANNED PHRASES (tools/humanize/gate.py on the script): PASS
```
HUMANIZE GATE: PASS
```
### 7. WORDS PER LINE: PASS
```
no limit set; counts: 7, 132, 208, 141, 167, 247, 161, 329, 168, 369, 352, 130, 149, 109, 151, 101, 208, 313, 920, 274, 146, 248, 583, 120, 180, 344, 185, 342, 203, 181, 233, 500, 243, 352, 349, 566, 225, 704, 363, 272, 403, 242, 283, 132, 453, 329, 206, 145, 231, 339, 402, 324, 167, 154, 112, 437, 227, 232, 220, 341, 213, 135, 230, 196, 186, 269, 329, 113, 700, 672, 104, 473, 371, 425, 415, 191, 195, 332, 1227, 279, 336, 290, 118, 275, 228, 209, 315, 115, 298, 881, 322, 290, 260, 94, 358, 201, 228, 191, 172, 159, 88, 175, 457, 344, 600, 634, 764, 687, 208, 536, 144, 179, 174, 144, 108, 276, 289, 35, 467, 2425, 90, 112, 126, 96, 123, 110, 96, 112, 103, 121, 118, 62, 278, 71, 46, 331, 355, 167, 174, 412, 241, 205, 153, 254, 304, 333, 180, 301, 204, 146, 87 (total 42994)
```
### 8. HEARD vs WRITTEN (strict word-for-word): PASS
```
similarity 1.000; identical after punctuation and case are removed
```
### 9. SCRIPTURE on screen vs KJV source (Psalms 1-150 (title line only; the Psalms are audio, see verse-check)): PASS
```
source line: the book of psalms
identical
```
### 10. SCRIPTURE spoken vs KJV source (Psalms 1-150 (title line only; the Psalms are audio, see verse-check)): PASS
```
ok 4/4 words 'the book of psalms...'
```

GATE: BLOCKED. 4 of 10 not PASS. Do NOT send to Starhead or Neko. Fix, rebuild, rerun.

## ADDENDUM from Claude (Nov 28 2026): the 4 FAILs are the planned ones, none is a defect
- Check 2 LOUDNESS: reads about -18 LUFS on purpose (sleep-master level, same audio as the Starhead-passed master; packet checksum identical, see evidence.md). proof.py expects -14 for a normal video.
- Check 3 BLACK FRAMES: proof.py lists black at 31696 to 31715 s. That is the planned fade to black over the final 60 s (the last scene fades from 31656 s). The brightness scan of all 31,716 frames (evidence.md) shows the body never goes below about 14 of 255 and the biggest frame-to-frame step is 1.4 levels, so there is no black anywhere else.
- Check 4 SILENT GAPS: only after 31650 s, the audio bed fading below -50 dB by design (same as the passed master).
- Check 5 FRAMES (4/5): proof.py cannot grab the last second of a 1 fps file. Saved by hand: frames/5_last.png (31714 s, black, the fade end) and frames/6_last_scene_before_fade.png (31640 s, the last scene still lit).
- Checks 6 to 10 PASS as before (title line only on screen; Psalms are audio).
