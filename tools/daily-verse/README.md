# Daily Verse Shorts (Neko, Nov 17 2026)
BLESSED MORNING = 5:00 AM ET, ends "Have a blessed day."
REST IN THE WORD = 7:30 PM ET, ends pointing to the KJV audio Bible readings (Psalms sleep reading, link in description).
Free: Pexels portrait footage (Chrome fetch of file URLs -> fetch-branch.yml temp branch tmp-nature2-1117), Kokoro am_michael, KJV text from aruljohn/Bible-kjv.
Build: KOKORO_DIR=<dir with kokoro-v1.0.onnx + voices-v1.0.bin> python3 build.py eps/<ep>.json <footage dir> <out.mp4>
Rules: KJV word-exact on screen, prayer ends in Jesus' name, no prayer requests, closer "Type amen, and send this to ...".
Footage list (m-* morning, n-* night): lake, birds, forest, waterfall, eagle / stars, moon, lake, ocean, candle. Skip n-lake1 (person on dock).

## Voice check (Nov 26 2026, after "goest" went out sounding like "ghost")
- Before building or queueing ANY new card: `KOKORO_DIR=<model dir> python3 tools/daily-verse/voicecheck.py`. It prints how the voice will sound out every word nobody has reviewed. FAIL = read the sounds, then `--accept` the right ones or add a fix.
- Fixes live in build.py `FIX` as SOUNDS (phonemes), never as a respelling. The verse on screen and in the description is never touched. Respelling makes it worse ("go-est" is read as letters).
- Prove every new fix by ear-machine, not Whisper: voice the line, 16 kHz mono wav into the repo, run phonemes.yml, read the phones from the draft release `inbox` (asset phones-<run>.json). Whisper writes the word it expects and hid all five Bible-word errors.
- Fixed so far: goest, hast, strengtheneth, Zephaniah, commune (verb), wind down, tear them down, live like, use the time, read slowly.
- A card that is already scheduled in Buffer keeps its old file until the post's video link is set again (same link with ?v=2 forces Buffer to fetch the new file; check durationMs changed).
