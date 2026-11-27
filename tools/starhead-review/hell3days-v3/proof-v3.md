# PROOF PACK for final_v3.mp4
built Nov 27 2026 02:24 PM ET | sha256 3f1687904c8333b3... | 21573975 bytes

| # | Check | Result |
|---|---|---|
| 1 | FILE (has video and audio, vertical, longer than 1s) | **PASS** |
| 2 | LOUDNESS (-14 LUFS +/-2, true peak at or under -1 dB) | **PASS** |
| 3 | BLACK FRAMES (none in the middle of the video) | **PASS** |
| 4 | SILENT GAPS (no full-mix silence of 1 s or more) | **PASS** |
| 5 | FRAMES (first, quarter, middle, three-quarter, last saved for the reviewer to LOOK at) | **PASS** |
| 6 | BANNED PHRASES (tools/humanize/gate.py on the script) | **PASS** |
| 7 | WORDS PER LINE (max 45) | **PASS** |
| 8 | HEARD vs WRITTEN (strict word-for-word) | **PASS** |
| 9 | SCRIPTURE on screen vs KJV source (Psalm 16:10; Colossians 2:15; Revelation 1:18) | **PASS** |
| 10 | SCRIPTURE spoken vs KJV source (Psalm 16:10; Colossians 2:15; Revelation 1:18) | **PASS** |

## Raw evidence
### 1. FILE (has video and audio, vertical, longer than 1s): PASS
```
duration 54.99s | video h264 1080x1920 | audio aac 48000 Hz
```
### 2. LOUDNESS (-14 LUFS +/-2, true peak at or under -1 dB): PASS
```
integrated -14.3 LUFS | true peak -1.49 dBTP | LRA 2.50
```
### 3. BLACK FRAMES (none in the middle of the video): PASS
```
none found (blackdetect d=0.2 pic_th=0.98; start/end fades ignored: 0)
```
### 4. SILENT GAPS (no full-mix silence of 1 s or more): PASS
```
none found (silencedetect -50 dB, 1 s). A voice dropout under a music bed is NOT caught here; that is the heard-vs-written check.
```
### 5. FRAMES (first, quarter, middle, three-quarter, last saved for the reviewer to LOOK at): PASS
```
5/5 frames in /tmp/work/build/proof_v3/frames; contact sheet /tmp/work/build/proof_v3/contact.png. Face, outfit, set, text, banned picture: reviewer eyes, not a script.
```
### 6. BANNED PHRASES (tools/humanize/gate.py on the script): PASS
```
HUMANIZE GATE: PASS
```
### 7. WORDS PER LINE (max 45): PASS
```
counts: 22, 26, 31, 35, 26
```
### 8. HEARD vs WRITTEN (strict word-for-word): PASS
```
similarity 1.000; identical after punctuation and case are removed
```
### 9. SCRIPTURE on screen vs KJV source (Psalm 16:10; Colossians 2:15; Revelation 1:18): PASS
```
source line: for thou wilt not leave my soul in hell neither wilt thou suffer thine holy one to see corruption and having spoiled principalities and powers he made a shew of them openly triumphing over them in it i am he that liveth and was dead and behold i am alive for evermore amen and have the keys of hell and of death
identical
```
### 10. SCRIPTURE spoken vs KJV source (Psalm 16:10; Colossians 2:15; Revelation 1:18): PASS
```
ok 19/19 words 'for thou wilt not leave my...'; ok 18/18 words 'and having spoiled principalities and powers...'; ok 25/25 words 'i am he that liveth and...'
```

GATE: PASS (10 of 10). Send to Starhead with the spec.
