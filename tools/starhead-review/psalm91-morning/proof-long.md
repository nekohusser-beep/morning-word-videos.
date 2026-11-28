# PROOF PACK for Psalm-91-Neko-Voice-Final.mp4
built Nov 28 2026 09:13 AM ET | sha256 5bcd446a2361eb9f... | 283696779 bytes

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
| 9 | SCRIPTURE on screen vs KJV source (8 passages: Psalm 91:1-2, 3-4, 5-8, John 16:33, Psalm 91:9-10, Proverbs 18:10, Psalm 91:11-13, 14-16) | **PASS** |
| 10 | SCRIPTURE spoken vs KJV source (8 passages: Psalm 91:1-2, 3-4, 5-8, John 16:33, Psalm 91:9-10, Proverbs 18:10, Psalm 91:11-13, 14-16) | **PASS** |

## Raw evidence
### 1. FILE (has video and audio, landscape, longer than 1s): PASS
```
duration 456.96s | video h264 1920x1080 | audio aac 48000 Hz
```
### 2. LOUDNESS (-14 LUFS +/-2, true peak at or under -1 dB): PASS
```
integrated -14.05 LUFS | true peak -1.63 dBTP | LRA 3.80
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
5/5 frames in proof_v5/frames; contact sheet proof_v5/contact.png. Face, outfit, set, text, banned picture: reviewer eyes, not a script.
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
### 9. SCRIPTURE on screen vs KJV source (8 passages: Psalm 91:1-2, 3-4, 5-8, John 16:33, Psalm 91:9-10, Proverbs 18:10, Psalm 91:11-13, 14-16): PASS
```
source line: he that dwelleth in the secret place of the most high shall abide under the shadow of the almighty i will say of the lord he is my refuge and my fortress my god in him will i trust surely he shall deliver thee from the snare of the fowler and from the noisome pestilence he shall cover thee with his feathers and under his wings shalt thou trust his truth shall be thy shield and buckler thou shalt not be afraid for the terror by night nor for the arrow that flieth by day nor for the pestilence that walketh in darkness nor for the destruction that wasteth at noonday a thousand shall fall at thy side and ten thousand at thy right hand but it shall not come nigh thee only with thine eyes shalt thou behold and see the reward of the wicked these things i have spoken unto you that in me ye might have peace in the world ye shall have tribulation but be of good cheer i have overcome the world because thou hast made the lord which is my refuge even the most high thy habitation there shall no evil befall thee neither shall any plague come nigh thy dwelling the name of the lord is a strong tower the righteous runneth into it and is safe for he shall give his angels charge over thee to keep thee in all thy ways they shall bear thee up in their hands lest thou dash thy foot against a stone thou shalt tread upon the lion and adder the young lion and the dragon shalt thou trample under feet because he hath set his love upon me therefore will i deliver him i will set him on high because he hath known my name he shall call upon me and i will answer him i will be with him in trouble i will deliver him and honour him with long life will i satisfy him and shew him my salvation
identical
```
### 10. SCRIPTURE spoken vs KJV source (8 passages: Psalm 91:1-2, 3-4, 5-8, John 16:33, Psalm 91:9-10, Proverbs 18:10, Psalm 91:11-13, 14-16): PASS
```
ok 39/39 words 'he that dwelleth in the secret...'; ok 38/38 words 'surely he shall deliver thee from...'; ok 69/69 words 'thou shalt not be afraid for...'; ok 31/31 words 'these things i have spoken unto...'; ok 30/30 words 'because thou hast made the lord...'; ok 17/17 words 'the name of the lord is...'; ok 51/51 words 'for he shall give his angels...'; ok 61/61 words 'because he hath set his love...'
```

GATE: PASS (10 of 10). Send to Starhead with the spec.
