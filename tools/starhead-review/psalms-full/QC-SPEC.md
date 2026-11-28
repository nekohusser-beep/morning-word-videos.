# STARHEAD QC JOB: Psalms 1 to 150, the full book in one video. Nov 28 2026, from Claude.
You are QC. Check cold against this spec. Answer PASS or FAIL with a reason per line (timestamp for every FAIL). You do not rebuild; a FAIL goes back to Claude. Neko gets the file only after your PASS, then he has the final say. NOTHING is posted until Neko says yes on this exact file.

## What this is
- Blessed Prayers long sleep reading: the whole book of Psalms, KJV, read by the same narrator as the six live Psalms parts. 8:48:36 (31716 s), 16:9, 1080p, 1 frame per second. The picture follows our sleep-reading standard: the gold title card "The Book of Psalms / Psalms 1 to 150 . King James Version . for rest" for the first 60 seconds (it fades out at about 0:50 to 0:55), then a plain dark screen (near-black, RGB about 7) for the rest of the file. There is no other picture.
- Neko asked for the six live Psalms parts (each under 110 minutes so they auto-dub) to be joined back into one video. Nothing was re-recorded and no word was changed. Parts 2 to 6 each had their 2 s lead-in silence trimmed; the pause at every join is about 3.57 s, which is the normal pause between psalms in these readings.
- Under the voice there is a quiet bed that fades out over the last 15 minutes. Narration ends at about 8:33:32 (30812 s) with "Praise ye the LORD." and the rest is the fading bed.
- No picture work, no thumbnail and no SEO in this pack. Nothing is posting.
- This is one 8 hour 49 minute file, so nobody can sit through all of it. The check is built from: (1) the machine word check on the whole file, (2) short clips at the five joins, the start and the end, which you watch and hear in full, (3) a 10-minute compilation of the 65 spots where the machines could not settle the pronunciation, which you listen to.

## Files (all in this folder; 480p/small review copies, the real master is the 391 MB 1080p file)
- sample-0-start-0m-to-2m.mp4: the first 2 minutes.
- sample-join-1-p1-to-p2.mp4 ... sample-join-5-p5-to-p6.mp4: 20 to 21 s around each join. The old psalm ends in the first 4 s, the pause runs to about 8 s, and the next psalm starts at 8 s into the clip.
- sample-psalm150-close.mp4: 80 s from 30770 s: the last verses of Psalm 150, the last words ("Praise ye the LORD." at about 42 s into the clip), then the bed alone.
- sample-end-last-2m.mp4: the last 2 minutes (31596 s to the end).
- psalms-spot-listen.mp4 (10:30) and spot-index.md: the 65 spots, in order, with what the script says and what the machines heard.
- title-frame.jpg: the title card (the only picture in the video). proof/frames/ has the 5 proof frames (first, quarter, middle, three-quarter, last); the last four are the plain dark screen.
- proof.md (proof.py output on the full master), reconcile-dispositions.md and dispositions.csv (every one of the 608 word differences the machines raised, with a reason), verse-check.md (every KJV verse against the script), script.txt (151 lines, as spoken, Psalms in [[ ]]), kjv_source.txt (KJV, one verse per line).

## Where the joins are (time in the full video)
1. 1:32:55 (5575 s): Psalm 31 ends "...all ye that hope in the LORD." then Psalm 32 starts.
2. 3:03:34 (11013.6 s): Psalm 56 ends "...in the light of the living?" then Psalm 57.
3. 4:33:36 (16416.3 s): Psalm 78 ends "...by the skilfulness of his hands." then Psalm 79.
4. 6:00:44 (21644.4 s): Psalm 104 ends "...Praise ye the LORD." then Psalm 105.
5. 7:33:06 (27185.5 s): Psalm 124 ends "...who made heaven and earth." then Psalm 125.
In each join clip the next psalm begins at about 8 s.

## What the machines already did (proof.py plus 36 speech-to-text runs). You do NOT redo these, but read proof.md.
- Speech-to-text on the finished audio, cut at chapter pauses into 18 pieces, each run twice (medium.en and large-v3, 36 runs, all finished). Raw: 608 places where a machine wrote something different from the script out of about 42,900 words. Every one is in dispositions.csv with its time, what each machine wrote and why it was accepted:
  - 172 spacing only (for ever / forever, loving kindness / lovingkindness).
  - 140 where the second machine heard the script word exactly.
  - 166 spelling variants: the machine writes the modern spelling of the same spoken word (shew/show, honour/honor, favour/favor, brake/break, reins/reigns, stedfast/steadfast, and so on).
  - 67 machine noise on a word it hears correctly elsewhere. Example: "hast" is in the book 189 times; the machines wrote "haste" at 24 of them and "hast" at the other 165, so the voice is not saying "haste" (two spots are in the spot-listen file so you can confirm). Same for "ye" written "he" (10 of 123), "Selah" written "salah" (4 of 71).
  - 1 ambience-only tail: after the last word the machines invent "Praise the LORD." every 30.0 s (30846 s onward). The audio there is the bed at -37 dB falling to -86 dB; there is no voice. Please confirm by ear on the end clip.
  - 1 script gap, fixed: the narrator says "The Book of Psalms, King James Version" at the start and the script line left out "The Book of". The script now has it.
  - 61 that the machines cannot judge: rare words, old verb endings and names where all three machines (medium.en, large-v3 and a third small model) write a modern or near spelling. These cannot be settled by software. They are the 65 clips in psalms-spot-listen.mp4 (the 61 plus two "hast" and two "ye" to confirm the noise above). This is where I need your ears.
- Every one of the 2,461 verses in the KJV source is found word for word, unbroken, in the script (verse-check.md). So script = KJV, and the speech-to-text says the narrator reads the script.
- The words are the same audio as the six live Psalms parts. Neko decided on Oct 15 to leave the live Psalms audio as it is (no re-voicing), so a mispronounced rare word you find is logged for Neko to decide, it is not a rebuild.

## Known flags in proof.md (expected, explained, NOT defects unless you hear something)
- LOUDNESS reads -18.2 LUFS, true peak -1.3 dBTP. proof.py expects -14 for a regular video. A sleep reading is made to the sleep-master level (-18 LUFS, quiet on purpose, same as the six live parts), so this is a false alarm for this kind of video. Please judge by ear that it is even and quiet, no spikes, no level jump at a join.
- BLACK FRAMES: proof.py reports PASS only because the one black segment starts at 0 and is treated as the start fade. In truth the screen is dark from about 0:55 to the end by design (sleep standard: 60 s title frame, then black). Nothing to fix.
- FRAMES: proof.py reports 4 of 5 saved because it cannot grab a frame at the exact last second of a 1 fps file; I saved the fifth by hand (proof/frames/5_last.png, 31714 s, plain dark).
- SILENT GAPS: proof.py lists silence only at 31650.5 s and later (31650.5 to 31668.5 s and on): that is the bed fading below -50 dB over the last minutes, by design (bed fade). Nothing is listed before 31650 s, so there is no silence of 1 s or more anywhere in the narrated 8 hours. The pauses between psalms are about 3.6 s with the bed running (about -37 dB), above the detector's -50 dB threshold.
- SCRIPTURE on screen: the Psalms are spoken only; the only text on screen is the title. The on-screen check was run on the title line alone, and the full verse check is in verse-check.md.

## What PASS looks like
1. JOINS (five clips): the psalm ends, a pause of about 3.6 s with the quiet bed running through it, the next psalm starts. No click or pop, no clipped or doubled word, no level jump, no gap that feels wrong, same voice and same room tone on both sides.
2. START (first 2 minutes): the title card shows from frame 1 and stays for the first minute (static is fine), then fades to the plain dark screen. The narrator says the title, "The Book of Psalms, King James Version", then Psalm 1. No stray sound at the very start.
3. END: Psalm 150 ends at about 30812 s (psalm150-close clip), and the end clip (last 2 minutes, starting at 31596 s) is the bed only. Confirm there is no voice, no "Praise the LORD" and no click, the bed fades out smoothly and the file ends cleanly. The last words are in sample-psalm150-close.mp4: confirm Psalm 150 closes with "Praise ye the LORD." and the bed then carries on quietly.
4. SPOT CLIPS (65): in each clip, the word named in spot-index.md is said clearly and correctly for the KJV word (rare names may be said the way a narrator would reasonably say them; flag only a word that is clearly wrong, cut off or doubled). Give clip numbers for anything you would fix.
5. TITLE CARD (title-frame.jpg): readable at phone size, no brand, no watermark, spelling right; plain dark screen after the first minute is correct. (The Bible with the steel square does not appear anywhere in this file.)
6. No prayer requests, no glorifying the dead, no promised future content, no ElevenLabs mention: n/a for a Bible reading with no added words; confirm the narrator adds nothing but the title.

## Things only you can sign off on (reply PASS or FAIL on each)
A. JOINS 1 to 5.  B. START.  C. END (tail is the bed only).  D. SPOT CLIPS 1 to 65 (list the clip numbers of any FAIL).  E. TITLE CARD.  F. LEVEL: quiet and even, no spikes (judged on the clips).

## Answer format
One line per item A to F plus a PASS/FAIL for the whole job. For each FAIL: the timestamp or clip number, what you heard, and what the fix should be. Then post the answer in this chat. If you cannot open a file, say which one; do not guess.

## Full script
script.txt in this folder (151 lines: the title, then Psalm 1 to Psalm 150, each in [[ ]] with "Psalm N." spoken first, Selah spoken where the KJV has it).
