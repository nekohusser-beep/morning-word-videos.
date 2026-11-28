# PROOF PACK for psalm91-final.mp4
built Nov 28 2026 01:33 AM ET | sha256 7d0707d0d2282f38... | 283167619 bytes

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
| 9 | SCRIPTURE on screen vs KJV source (Psalm 91:1-16; John 16:33; Proverbs 18:10) | **PASS** |
| 10 | SCRIPTURE spoken vs KJV source (Psalm 91:1-16; John 16:33; Proverbs 18:10) | **PASS** |

## Raw evidence
### 1. FILE (has video and audio, landscape, longer than 1s): PASS
```
duration 457.73s | video h264 1920x1080 | audio aac 48000 Hz
```
### 2. LOUDNESS (-14 LUFS +/-2, true peak at or under -1 dB): PASS
```
integrated -14.11 LUFS | true peak -1.53 dBTP | LRA 4.20
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
5/5 frames in /home/claude/ps91/proof/frames; contact sheet /home/claude/ps91/proof/contact.png. Face, outfit, set, text, banned picture: reviewer eyes, not a script.
```
### 6. BANNED PHRASES (tools/humanize/gate.py on the script): PASS
```
HUMANIZE GATE: PASS
```
### 7. WORDS PER LINE: PASS
```
no limit set; counts: 52, 37, 11, 39, 54, 32, 4, 38, 38, 33, 4, 69, 49, 45, 31, 8, 30, 19, 17, 24, 4, 51, 56, 47, 18, 61, 31, 36, 12, 77, 21 (total 1048)
```
### 8. HEARD vs WRITTEN (strict word-for-word): PASS
```
similarity 1.000; identical after punctuation and case are removed
```
### 9. SCRIPTURE on screen vs KJV source (Psalm 91:1-16; John 16:33; Proverbs 18:10): PASS
```
source line: he that dwelleth in the secret place of the most high shall abide under the shadow of the almighty i will say of the lord he is my refuge and my fortress my god in him will i trust surely he shall deliver thee from the snare of the fowler and from the noisome pestilence he shall cover thee with his feathers and under his wings shalt thou trust his truth shall be thy shield and buckler thou shalt not be afraid for the terror by night nor for the arrow that flieth by day nor for the pestilence that walketh in darkness nor for the destruction that wasteth at noonday a thousand shall fall at thy side and ten thousand at thy right hand but it shall not come nigh thee only with thine eyes shalt thou behold and see the reward of the wicked these things i have spoken unto you that in me ye might have peace in the world ye shall have tribulation but be of good cheer i have overcome the world because thou hast made the lord which is my refuge even the most high thy habitation there shall no evil befall thee neither shall any plague come nigh thy dwelling the name of the lord is a strong tower the righteous runneth into it and is safe for he shall give his angels charge over thee to keep thee in all thy ways they shall bear thee up in their hands lest thou dash thy foot against a stone thou shalt tread upon the lion and adder the young lion and the dragon shalt thou trample under feet because he hath set his love upon me therefore will i deliver him i will set him on high because he hath known my name he shall call upon me and i will answer him i will be with him in trouble i will deliver him and honour him with long life will i satisfy him and shew him my salvation
identical
```
### 10. SCRIPTURE spoken vs KJV source (Psalm 91:1-16; John 16:33; Proverbs 18:10): PASS
```
ok 39/39 words 'he that dwelleth in the secret...'; ok 38/38 words 'surely he shall deliver thee from...'; ok 69/69 words 'thou shalt not be afraid for...'; ok 31/31 words 'these things i have spoken unto...'; ok 30/30 words 'because thou hast made the lord...'; ok 17/17 words 'the name of the lord is...'; ok 51/51 words 'for he shall give his angels...'; ok 61/61 words 'because he hath set his love...'
```

GATE: PASS (10 of 10). Send to Starhead with the spec.


## Added by hand (the workflow asks for these in the pack). ROUND 3, Nov 28 2026
### What changed from Round 2
- 0:00 to 0:35 is now an AI avatar of Neko (Google Flow, from his hoodie photo) speaking the old opening lines; the voice is Neko's own, made with Seed-VC from the Flow voice. 6:46 to 7:31 is the same avatar saying the prayer and the closer, then the end card to 7:37.7. The teaching between (0:35 to 6:46) is the Round 2 narrator, footage, Scripture cards and music, unchanged.
- Total 457.73 s (7:37.7), 13,732 frames at 30 fps, 1080p. The spoken script is word for word the Round 2 script (check 8).
- Two readable aircraft posters on the wall behind the avatar ("AIRBUS A350", "BOEING 747") were blurred out in every avatar shot (re-rendered, concatenated, checked by looking at frames and by OCR of the poster band). The KI hoodie print is Neko's own Kingdom Impact Shop design and was left in.

### Avatar voice and lips (12 clips, tools: CAMPPlus speaker model, the one Seed-VC uses; YIN pitch; envelope lag against the Flow source)
- Speaker similarity to Neko's 19 s reference: converted clips 0.80 to 0.88 (mean 0.84); the same clips before conversion, the Flow voice, were 0.46 to 0.60 (mean 0.51).
- Lip sync: conversion keeps duration exactly, so the mouth stays in time. Speech-envelope lag against the Flow source is 0 to 10 ms (a video frame is 33 ms). 11 of 12 clips have envelope correlation 0.89 to 0.97; "and on the way to jobs" is 0.77.
- Steady voice across the 12 clips: median pitch 84 to 102 Hz, speech level -15.7 to -18.5 dBFS before the master chain; the master chain (high-pass, light compressor, loudness normalise) evens them. One clip was re-converted because Seed-VC turned "psalm" into "song"; the redo reads "This Psalm" on speech-to-text.
- Words: every clip also checked word for word by a local speech-to-text pass on the converted audio, then the whole finished audio by both big models (below).

### Transcript hygiene (heard.txt = medium.en reconciled with large-v3, both run on the FINISHED Round 3 audio by transcribe.yml, runs 46115151954 and 46115153921)
Accepted differences, every one logged:
```
stray word, second pass did not hear it (model artifact, ASR-only; ask the human ear): first pass inserted 'but' after 'fortress my god'
KJV spelling, same sound: wrote 'flieth' / heard 'flyeth'
KJV spelling, same sound: wrote 'honour' / heard 'honor'
KJV spelling, same sound: wrote 'shew' / heard 'show'
```
- The one real question is at 0:55 (verse 2, "my God; in him will I trust"): medium.en heard a "but" before "in him". large-v3 did not hear it, and a third pass (a small local model on the 51 to 61 s window of the final audio) reads "My God, in Him will I trust." This stretch is the unchanged Round 2 narrator audio, where the same line passed Round 2. Reviewer: listen at 0:55.
- "KJV spelling, same sound" is a rule in the local norm_heard_kjv.py (honour/honor, shew/show, flieth/flyeth are one spoken word; Whisper writes the modern spelling). Logged so the reviewer can overrule it.

### What is really on the screen (OCR of the finished video, one frame from the middle of each verse page, right panel only, tesseract)
| Page | Time | OCR words | OCR equals the KJV page text |
|---|---|---|---|
| Psalm 91:1-2 | 0:50 | 39 | yes |
| Psalm 91:3-4 | 1:47 | 38 | yes |
| Psalm 91:5-8 | 2:36 | 34 | yes |
| Psalm 91:5-8 | 2:49 | 35 | yes |
| John 16:33 | 3:40 | 31 | yes |
| Psalm 91:9-10 | 4:00 | 30 | yes |
| Proverbs 18:10 | 4:22 | 18 | yes (OCR read the header line as a word, see note) |
| Psalm 91:11-13 | 4:49 | 32 | yes |
| Psalm 91:11-13 | 4:58 | 19 | yes |
| Psalm 91:14-16 | 6:03 | 35 | yes |
| Psalm 91:14-16 | 6:13 | 26 | yes |

(Proverbs 18:10 at 4:22: the OCR read the header line "PROVERBS 18:10" as a word; the verse text on the card equals the KJV.)

### IQ Vid pre-post check (tools/iqvid/prepost.py on SEO-long.md + captions.srt, keyword "psalm 91 prayer")
0 to fix, 20 passed, 2 to do. (1) The tool could not load its KJV library here, so the four KJV lines in the description were checked by hand against the live KJV source: word for word. (2) At upload: end screen on "He Healed Ten Lepers. Only One Said Thank You.", and set "Altered content" to YES in Studio.
