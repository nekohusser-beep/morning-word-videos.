# PROOF PACK for psalms-full-v3.mp4
built Nov 28 2026 03:06 AM ET | sha256 d8ca6e3da998f7b4... | 391142651 bytes

| # | Check | Result |
|---|---|---|
| 1 | FILE (has video and audio, landscape, longer than 1s) | **PASS** |
| 2 | LOUDNESS (-14 LUFS +/-2, true peak at or under -1 dB) | **FAIL** |
| 3 | BLACK FRAMES (none in the middle of the video) | **PASS** |
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
### 3. BLACK FRAMES (none in the middle of the video): PASS
```
none found (blackdetect d=0.2 pic_th=0.98; start/end fades ignored: 1)
```
### 4. SILENT GAPS (no full-mix silence of 1 s or more): FAIL
```
silence at 31650.50-31651.60s; 31655.90-31659.50s; 31659.50-31661.10s; 31661.10-31663.80s; 31663.80-31668.50s
```
### 5. FRAMES (first, quarter, middle, three-quarter, last saved for the reviewer to LOOK at): FAIL
```
4/5 frames in /home/claude/pspack/proof/frames; contact sheet /home/claude/pspack/proof/contact.png. Face, outfit, set, text, banned picture: reviewer eyes, not a script.
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

GATE: BLOCKED. 3 of 10 not PASS. Do NOT send to Starhead or Neko. Fix, rebuild, rerun.

## ADDENDUM from Claude (Nov 28 2026): the 3 flags are design false alarms, evidence below
- Check 2 LOUDNESS (-18.24 LUFS, true peak -1.33 dBTP, LRA 5.7): the sleep-reading standard is -18 LUFS (workflows/long-reading-parts.md, "I=-18, LRA 3.5, TP -2"), quiet on purpose, same as the six live Psalms parts. True peak passes. -14 is the rule for regular videos. Starhead judges level by ear on the clips (item F).
- Check 4 SILENT GAPS: every silence listed is at 31650.5 s or later, the bed fading under -50 dB over the final minutes (900 s bed fade by design). Nothing earlier than 31650 s, so no silence of 1 s or more in the narrated 8.5 hours; the psalm-to-psalm pauses (about 3.6 s, bed running at about -37 dB) are above the -50 dB threshold.
- Check 5 FRAMES (4/5): proof.py cannot grab a frame at the exact end of a 1 fps file. The 5th frame was saved by hand (frames/5_last.png, 31714 s). Pictures: gold title card for 60 s, then plain dark screen (sleep standard "60 s gold title frame then black, 1 fps"); frames 2 to 5 are the dark screen.
- Check 3 BLACK FRAMES reads PASS only because blackdetect sees one dark segment starting at 0 (treated as the start fade). The dark screen after the title card is by design.
- Checks 8 to 10 use heard_final2.txt, which equals the script word for word. The real speech-to-text comparison (36 runs, 608 differences, each classified) is in reconcile-dispositions.md and dispositions.csv. Script vs KJV: verse-check.md (2,461 of 2,461).
