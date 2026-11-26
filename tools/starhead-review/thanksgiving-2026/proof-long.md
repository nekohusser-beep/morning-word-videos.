# PROOF PACK for Where-Are-the-Nine-Thanksgiving-Word.mp4
built Nov 26 2026 12:16 PM ET | sha256 7067b9a4af7a9dbb... | 225672662 bytes

| # | Check | Result |
|---|---|---|
| 1 | FILE (has video and audio, landscape, longer than 1s) | **PASS** |
| 2 | LOUDNESS (-14 LUFS +/-2, true peak at or under -1 dB) | **PASS** |
| 3 | BLACK FRAMES (none in the middle of the video) | **PASS** |
| 4 | SILENT GAPS (no full-mix silence of 1 s or more) | **PASS** |
| 5 | FRAMES (first, quarter, middle, three-quarter, last saved for the reviewer to LOOK at) | **PASS** |
| 6 | BANNED PHRASES (tools/humanize/gate.py on the script) | **PASS** |
| 7 | WORDS PER LINE | **PASS** |
| 8 | HEARD vs WRITTEN (strict word-for-word) | **PASS** |
| 9 | SCRIPTURE on screen vs KJV source (10 verses (see table)) | **PASS** |
| 10 | SCRIPTURE spoken vs KJV source (10 verses (see table)) | **PASS** |

## Raw evidence
### 1. FILE (has video and audio, landscape, longer than 1s): PASS
```
duration 610.23s | video h264 1920x1080 | audio aac 48000 Hz
```
### 2. LOUDNESS (-14 LUFS +/-2, true peak at or under -1 dB): PASS
```
integrated -14.17 LUFS | true peak -1.25 dBTP | LRA 2.90
```
### 3. BLACK FRAMES (none in the middle of the video): PASS
```
none found (blackdetect d=0.2 pic_th=0.98; start/end fades ignored: 1)
```
### 4. SILENT GAPS (no full-mix silence of 1 s or more): PASS
```
none found (silencedetect -50 dB, 1 s). A voice dropout under a music bed is NOT caught here; that is the heard-vs-written check.
```
### 5. FRAMES (first, quarter, middle, three-quarter, last saved for the reviewer to LOOK at): PASS
```
5/5 frames in proof_final_long2/frames; contact sheet proof_final_long2/contact.png. Face, outfit, set, text, banned picture: reviewer eyes, not a script.
```
### 6. BANNED PHRASES (tools/humanize/gate.py on the script): PASS
```
HUMANIZE GATE: PASS
```
### 7. WORDS PER LINE: PASS
```
no limit set; counts: 45, 49, 38, 10, 16, 45, 55, 61, 52, 6, 40, 12, 37, 7, 10, 61, 38, 16, 10, 26, 17, 12, 19, 39, 27, 46, 19, 27, 17, 24, 40, 39, 83, 20, 17, 60, 38, 54, 16, 41, 37, 2, 130, 33 (total 1491)
```
### 8. HEARD vs WRITTEN (strict word-for-word): PASS
```
similarity 1.000; identical after punctuation and case are removed
```
### 9. SCRIPTURE on screen vs KJV source (10 verses (see table)): PASS
```
source line: o give thanks unto the lord for he is good for his mercy endureth for ever jesus master have mercy on us and one of them when he saw that he was healed turned back and with a loud voice glorified god and fell down on his face at his feet giving him thanks and he was a samaritan were there not ten cleansed but where are the nine arise go thy way thy faith hath made thee whole bless the lord o my soul and forget not all his benefits every good gift and every perfect gift is from above and cometh down from the father of lights with whom is no variableness neither shadow of turning because that when they knew god they glorified him not as god neither were thankful but became vain in their imaginations and their foolish heart was darkened be careful for nothing but in every thing by prayer and supplication with thanksgiving let your requests be made known unto god and the peace of god which passeth all understanding shall keep your hearts and minds through christ jesus in every thing give thanks for this is the will of god in christ jesus concerning you
identical
```
### 10. SCRIPTURE spoken vs KJV source (10 verses (see table)): PASS
```
ok 16/16 words 'o give thanks unto the lord...'; ok 6/6 words 'jesus master have mercy on us...'; ok 37/37 words 'and one of them when he...'; ok 10/10 words 'were there not ten cleansed but...'; ok 10/10 words 'arise go thy way thy faith...'; ok 12/12 words 'bless the lord o my soul...'; ok 27/27 words 'every good gift and every perfect...'; ok 27/27 words 'because that when they knew god...'; ok 40/40 words 'be careful for nothing but in...'; ok 17/17 words 'in every thing give thanks for...'
```

GATE: PASS (10 of 10). Send to Starhead with the spec.
