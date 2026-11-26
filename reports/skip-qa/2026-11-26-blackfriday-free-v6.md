VERDICT: PASS

Third-pass review of the final re-render of `adhd/stack/skip-big-09-blackfriday-free.mp4` (file time 12:48, 1080x1920, 30 fps, 615 frames, 20.5 s). All frames re-extracted from this file. No BLOCKER and no SHOULD FIX remaining. Audio was not heard; speech timing is from a per-frame level trace of the file's own audio, which is sample-identical to the previous render.

## Fix status of the last pass's SHOULD FIX items

- **Line 3 caption sync: FIXED.** "I GOT IT!" lights I 310, GOT 315, IT! 322 (speech 311-324) and holds through the pause; "$299!" appears on frame 343 (11.43 s), 2 frames ahead of the speech onset at 345.
- **Line 4 caption sync: FIXED.** "IT'S $249 ONLINE." stays up to frame 448; "FREE SHIPPING." appears on frame 449 (14.97 s), exactly on the speech onset; SHIPPING lights at 456.
- **Line 2 caption sync: FIXED.** "SINCE THANKSGIVING." 186-222, "I LEFT BEFORE" 223-237, "THE PIE." 238-257 with PIE lit from 242 (before the 247-257 pause), "THAT'S SACRIFICE." starts on frame 258 (8.60 s), exactly on the speech onset.
- **Wide captions at the right edge: FIXED.** Widest caption is now "SINCE THANKSGIVING." at about x 100-975; "SINCE YESTERDAY?", "THAT'S SACRIFICE." and "IT'S $249 ONLINE." all sit inside the 100 px side margins.

## Defects (all NOTE)

1. **NOTE - line 0 caption still splits a sentence:** "3 A.M. 14" / "HOURS IN LINE." (0-0.87 s). Line 5 breaks mid-phrase ("DID THEY AT" / "LEAST HAVE PIE" / "ONLINE?"). Timing on both is correct; only the break points are awkward.
2. **NOTE - "$249" highlight is about 5 frames late.** It lights at frame 411 (13.70 s); the level trace shows "two" starting at about 406. Not noticeable at speed.
3. **NOTE - "SINCE THANKSGIVING." sits exactly on the 100 px margin** on the left and covers Dre's hand and the bottom of his flask (not a face, price or phone).
4. **NOTE - end card top line touches the bottom edge of the TV box,** about 55 px under the "$299"; price fully clear.
5. **NOTE - line 4 mouth size.** Skip's mouth moves on 397-467 in step with speech; about 70 x 35 px, readable at phone size but small.
6. **NOTE - Dre has a black cap of hair with a fade, not a fully bald head.** Consistent in all six shots, goatee always present.
7. **NOTE - end card picture starts on frame 559 (18.633 s),** one frame after the chime (558) and after the 18.60 s in `line-times.txt`.
8. **NOTE - three pack files were not regenerated** (`line-times.txt`, `voice-match.txt`, `clarity-all-takes.txt`, all 12:37). They still apply because the voice track is unchanged. `render.txt`, `loudness.txt`, `silences.txt` are 12:48 and agree with my measurements.
9. **NOTE - clarity, u001 (bfrB2):** "Dre!" recognised at 0.40 confidence, "You" heard as "You've". u003 and u004 read correctly.

## What I checked on this render

- **Method:** all 615 frames extracted; contact sheets of every 3rd frame for the whole video; every frame at 111-116, 183-188, 307-312, 393-398, 485-490, 556-561; full-resolution caption crops with 100 px guide lines at frames 120, 145, 165, 200, 230, 245, 270, 330, 360, 410, 455, 530; per-frame audio level; exact frame of every caption highlight change, compared with `render.txt`.
- **Caption sync, other lines:** line 0 highlights at 0.00, 0.23, 0.60, 0.87, 1.30, 1.53, 1.97, 2.33, 2.60, 2.83 s, in step with the level trace and `render.txt`. Line 1 (read from the sheets): "DRE." from 114, "YOU BEEN HERE" by 138 (speech resumes 136), "SINCE YESTERDAY?" by 156, cleared by 177. Line 5 highlights at 16.27, 16.50, 16.73, 16.87, 17.13, 17.37, 17.53 s, ending with the speech at 17.97 s. Lines 0, 2, 3, 4, 5 match `render.txt` within about one frame.
- **Coverage:** no caption or end card touches a face, the $299 box price, the $249 phone or a sign; none is cut by the frame. Spelling and wording match the script.
- **Cuts:** frames 114, 186, 310, 396, 488 are clean single-frame cuts; end card dims cleanly on 559. No flash, stray frame, carried caption, or hook card on the wrong shot ("DRE CAMPED OUT" ends on 113).
- **Mouths (from the every-3rd-frame sheets):** speaker moves on every line; non-speaker still in both wide shots; no mouth motion seen in pauses or under the end card.
- **First 3 s:** top text from frame 0: "BLACK FRIDAY" 0-35, "3 A.M." 36-71, "DRE CAMPED OUT" 72-113.
- **Whole-video spot check:** no smears, patches, floating objects or garbled sign text; characters consistent; no new defect found.
- **Audio (measured on this file):** -15.1 LUFS, LRA 5.2 LU, true peak -1.3 dBFS. Voice-match 6/6 PASS per the pack. Chime under the end card from frame 558 at about -25 dB, decaying by about 20.2 s. Longest gap between lines about 0.63 s; gap before the chime about 0.7 s.
