# PROOF PACK for Where-Are-the-Nine-Short.mp4
built Nov 26 2026 07:08 AM ET | sha256 770efd7933e05b00... | 18998874 bytes

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
| 9 | SCRIPTURE on screen vs KJV source (Luke 17:17; Psalm 107:1) | **PASS** |
| 10 | SCRIPTURE spoken vs KJV source (Luke 17:17; Psalm 107:1) | **PASS** |

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
5/5 frames in /home/claude/tgs/proof2/frames; contact sheet /home/claude/tgs/proof2/contact.png. Face, outfit, set, text, banned picture: reviewer eyes, not a script.
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
### 9. SCRIPTURE on screen vs KJV source (Luke 17:17; Psalm 107:1): PASS
```
source line: were there not ten cleansed but where are the nine o give thanks unto the lord for he is good for his mercy endureth for ever
identical
```
### 10. SCRIPTURE spoken vs KJV source (Luke 17:17; Psalm 107:1): PASS
```
ok 10/10 words 'were there not ten cleansed but...'; ok 16/16 words 'o give thanks unto the lord...'
```

GATE: PASS (10 of 10). Send to Starhead with the spec.

## Evidence notes (added by Claude)
**Scripture source:** thiagobodruk/bible en_kjv.json (KJV).

### Verse table (Short, 2 verses)
| Verse | Result | Words | On-screen is exact KJV run | Same as script | Spoken unbroken | Omitted lead-in | Omitted tail |
|---|---|---|---|---|---|---|---|
| Luke 17:17 | **PASS** | 10 | True | True | True | and jesus answering said | - |
| Psalm 107:1 | **PASS** | 16 | True | True | True | - | - |

### Heard vs written
```
spacing only: wrote 'for ever' / heard 'forever'
LEFT AS DIFF: insert wrote '' / heard 'amen'
EVIDENCE for the one extra 'amen' (Whisper double-reads one drawn-out word): voice-only track voice_s.wav energy between 50.8 and 51.9 s is ONE continuous burst (51.0-51.6 s), not two; dropped from the reconciled transcript.
```
The transcript showed 'amen' twice at the end; that is a Whisper artifact (one energy burst in the voice-only track), dropped with the evidence logged. The script says it once.

### Footage
Full-video OCR scan every 1 s: no store, brand or logo text. The crowd clip with store signs was swapped for a silhouette walking at sunset. Audio unchanged since the speech check.
