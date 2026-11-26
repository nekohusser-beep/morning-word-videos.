# PROOF PACK for Where-Are-the-Nine-Thanksgiving-Word.mp4
built Nov 26 2026 07:06 AM ET | sha256 1ec56b310ef5cca3... | 229108927 bytes

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
integrated -14.2 LUFS | true peak -1.25 dBTP | LRA 2.90
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
5/5 frames in /home/claude/tgl/proof_long3/frames; contact sheet /home/claude/tgl/proof_long3/contact.png. Face, outfit, set, text, banned picture: reviewer eyes, not a script.
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

## Evidence notes (added by Claude)
**Scripture source:** thiagobodruk/bible en_kjv.json (KJV). Spoken and on-screen text compared word for word with it.

### Verse table (long video, 10 verses)
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
medium.en is the strict pass, large-v3 the independent second pass. A difference is cleared only when it is spacing, digits vs spelled numbers, or the second model heard the written word. Log:
```
spacing only: wrote 'for ever' / heard 'forever'
second pass heard it as written: wrote 'they're' / first pass heard 'they are'
spacing only: wrote 'every thing' / heard 'everything'
digits vs words: wrote 'two thousand' / heard '2000'
digits vs words: wrote 'first' / heard '1'
spacing only: wrote 'every thing' / heard 'everything'
second pass heard it as written: wrote 'in' / first pass heard 'and'
spacing only: wrote 'every thing' / heard 'everything'
spacing only: wrote 'every thing' / heard 'everything'
LEFT AS DIFF: insert wrote '' / heard 'you'
tail artifact dropped: medium.en added 'you' at 607.18 s; narration ends at 602.98 s, the narration-only track is silent there (rms 0.0) and large-v3 did not hear it. Whisper invents a word over the closing music.
```
Why one 'you' was dropped: medium.en invented it at 607.18 s. The narration ends at 602.98 s, the narration-only track is silent there (rms 0.0), and large-v3 did not hear it. Whisper adds words over the closing music.

### Pronunciation
'uses' in "the exact word the psalm uses" came out as yoo-siss. Fixed with a phoneme override and proven on a GitHub runner with wav2vec2 phones: before `j uː s ɪ z`, after `j uː z ᵻ z`.

### Footage
Full-video OCR scan every 2 s on the picture area: no store, brand or logo text left (two clips with store signs and a truck logo were swapped out). Free Pexels footage, one clip set per paragraph (plan.py).

### IQ Vid pre-post (tools/iqvid/prepost.py)
0 to fix, 2 to do at upload (scripture check by hand: done against the KJV json; end screen on the next video). Title A: He Healed Ten Lepers. Only One Said Thank You.
