# PROOF PACK for Where-Are-the-Nine-Short.mp4
built Nov 26 2026 12:00 PM ET | sha256 05422b42e7889902... | 19017207 bytes

| # | Check | Result |
|---|---|---|
| 1 | FILE (has video and audio, vertical, longer than 1s) | **PASS** |
| 2 | LOUDNESS (-14 LUFS +/-2, true peak at or under -1 dB) | **PASS** |
| 3 | BLACK FRAMES (none in the middle of the video) | **PASS** |
| 4 | SILENT GAPS (no full-mix silence of 1 s or more) | **PASS** |
| 5 | FRAMES (first, quarter, middle, three-quarter, last saved for the reviewer to LOOK at) | **PASS** |
| 6 | BANNED PHRASES (tools/humanize/gate.py on the script) | **PASS** |
| 7 | WORDS PER LINE | **PASS** |
| 8 | HEARD vs WRITTEN (strict word-for-word) | **PASS** |
| 9 | SCRIPTURE on screen vs KJV source (2 verses (see table)) | **PASS** |
| 10 | SCRIPTURE spoken vs KJV source (2 verses (see table)) | **PASS** |

## Raw evidence
### 1. FILE (has video and audio, vertical, longer than 1s): PASS
```
duration 59.43s | video h264 1080x1920 | audio aac 48000 Hz
```
### 2. LOUDNESS (-14 LUFS +/-2, true peak at or under -1 dB): PASS
```
integrated -14.41 LUFS | true peak -1.44 dBTP | LRA 1.60
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
5/5 frames in tgs/proof_final_short/frames; contact sheet tgs/proof_final_short/contact.png. Face, outfit, set, text, banned picture: reviewer eyes, not a script.
```
### 6. BANNED PHRASES (tools/humanize/gate.py on the script): PASS
```
HUMANIZE GATE: PASS
```
### 7. WORDS PER LINE: PASS
```
no limit set; counts: 24, 10, 35, 4, 16, 23, 23, 11 (total 146)
```
### 8. HEARD vs WRITTEN (strict word-for-word): PASS
```
similarity 1.000; identical after punctuation and case are removed
```
### 9. SCRIPTURE on screen vs KJV source (2 verses (see table)): PASS
```
source line: were there not ten cleansed but where are the nine o give thanks unto the lord for he is good for his mercy endureth for ever
identical
```
### 10. SCRIPTURE spoken vs KJV source (2 verses (see table)): PASS
```
ok 10/10 words 'were there not ten cleansed but...'; ok 16/16 words 'o give thanks unto the lord...'
```

GATE: PASS (10 of 10). Send to Starhead with the spec.

## Evidence notes (added by Claude), ROUND 2 build
**Scripture source:** thiagobodruk/bible en_kjv.json (KJV).

### Verse table (Short, 2 verses)
| Verse | Result | Words | On-screen is exact KJV run | Same as script | Spoken unbroken | Omitted lead-in | Omitted tail |
|---|---|---|---|---|---|---|---|
| Luke 17:17 | **PASS** | 10 | True | True | True | and jesus answering said | - |
| Psalm 107:1 | **PASS** | 16 | True | True | True | - | - |

### Heard vs written
```
spacing only: wrote 'for ever' / heard 'forever'
```
large-v3 adds "Amen. Amen." at 57.7 s (the Short's narration ends about 56 s and the narration-only track is silent from 56.5 s, rms 0.0); medium.en hears neither. The real "amen" of the prayer is at about 51 s and is said once. Whisper invents words over the closing music. Confirm by ear.

### Footage
Round 1 blocker: the gas-station canopy ("amigo") at 0:25-0:28. That slot is now a no-sign sunrise clip; a baked-in green dot in that stock clip was removed. OCR cannot read small stylised signs, so the real brand check is yours; Claude also looked at the frames on a contact sheet. Audio unchanged since the speech check.
