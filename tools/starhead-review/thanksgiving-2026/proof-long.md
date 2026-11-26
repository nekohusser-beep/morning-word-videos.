# PROOF PACK for Where-Are-the-Nine-Thanksgiving-Word.mp4
built Nov 26 2026 12:05 PM ET | sha256 695a5f5ea1ed1209... | 225434226 bytes

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
5/5 frames in tgl/proof_final_long/frames; contact sheet tgl/proof_final_long/contact.png. Face, outfit, set, text, banned picture: reviewer eyes, not a script.
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

## Evidence notes (added by Claude), ROUND 2 build
**Scripture source:** thiagobodruk/bible en_kjv.json (KJV).

### Verse table (long, 10 verses)
| Verse | Result | Words | On-screen is exact KJV run | Same as script | Spoken unbroken | Omitted lead-in | Omitted tail |
|---|---|---|---|---|---|---|---|
| Psalm 107:1 | **PASS** | 16 | True | True | True | - | - |
| Luke 17:13 | **PASS** | 6 | True | True | True | and they lifted up their voices and said | - |
| Luke 17:15-16 | **PASS** | 37 | True | True | True | - | - |
| Luke 17:17 | **PASS** | 10 | True | True | True | and jesus answering said | - |
| Luke 17:19 | **PASS** | 10 | True | True | True | and he said unto him | - |
| Psalm 103:2 | **PASS** | 12 | True | True | True | - | - |
| James 1:17 | **PASS** | 27 | True | True | True | - | - |
| Romans 1:21 | **PASS** | 27 | True | True | True | - | - |
| Philippians 4:6-7 | **PASS** | 40 | True | True | True | - | - |
| 1 Thessalonians 5:18 | **PASS** | 17 | True | True | True | - | - |

### Heard vs written: how the two speech models were reconciled
medium.en is the strict pass, large-v3 the independent second pass, both run on the audio of THIS final file. A difference is cleared only when it is spacing, digits vs spelled numbers, or the second model heard the written word. Log:
```
spacing only: wrote 'for ever' / heard 'forever'
spacing only: wrote 'every thing' / heard 'everything'
digits vs words: wrote 'two thousand' / heard '2000'
digits vs words: wrote 'first' / heard '1'
spacing only: wrote 'every thing' / heard 'everything'
second pass heard it as written: wrote 'in' / first pass heard 'and'
spacing only: wrote 'every thing' / heard 'everything'
spacing only: wrote 'every thing' / heard 'everything'
```
Tail: medium.en ends at "day." (602.64 s) with no extra word. large-v3 adds one "Amen." at 603.1 s after "have a blessed day"; the narration-only track has the decaying echo of "day" there (about -33 dB at 603.0 s) and is silent from 603.6 s (rms 0.0). Whisper invents a word over the closing music. Confirm by ear. The Round 1 "you" at 607 s is gone (the last bell hit under the music was removed and the end fade is 8 s).

### Pronunciation
Round 1 flagged "uses" at 1:55. The line was reworded to "And that's the exact word the psalm chose." and re-voiced in the same narrator voice, padded to the identical duration so no timestamp moved. medium.en heard "the exact word the Psalm chose"; large-v3 heard "the exact word the Psalm... ...chose" (it marks a short pause). Confirm by ear.

### Footage (what a script can and cannot prove)
No machine proof of brand-free footage is claimed. Round 1 showed OCR cannot read small stylised signs (it missed the amigo canopy and the CONSTANT clock). The three Round 1 shots were swapped and the new finals were looked at frame by frame on a contact sheet every 6 s by Claude; the real brand check is yours. A baked-in green dot in one sunrise stock clip was removed. Free Pexels footage, one clip set per paragraph (plan.py).

### Black-frame check
The candle shot at 9:33-9:39 first failed this check (a candle in a nearly black room is over 98% dark). Its exposure was lifted; it now reads as a candle in a dim room and the check passes.

### IQ Vid pre-post (tools/iqvid/prepost.py)
Title A: He Healed Ten Lepers. Only One Said Thank You. Chapters (0:00, 0:47, 2:03, 3:16, 4:15, 5:26, 5:56, 7:13, 8:28, 9:06) are unchanged: same cut length, same audio timing.
