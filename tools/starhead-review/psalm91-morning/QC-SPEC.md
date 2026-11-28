# STARHEAD QC JOB: Psalm 91 morning prayer, long video "Before You Walk Out the Door". ROUND 3, Nov 28 2026, from Claude.
You are QC. Check cold against this spec. Answer PASS or FAIL with a reason per line (timestamp for every FAIL). You do not rebuild; a FAIL goes back to Claude. Neko gets the file only after your PASS, then he has the final say. NOTHING is posted until Neko says yes on the exact file.

## ROUND 3 (Nov 28 2026): what changed since your Round 2
Neko asked for his own face and voice on the open and the close. Everything between is the Round 2 cut (same footage, narrator, Scripture cards, captions, music), unchanged. Answer A to J on THIS version; A to H are unchanged except where they touch the new parts, so a quick confirm is enough there. Items I and J are new and need a full look.
- 0:00 to 0:35 (0:35.47): an AI avatar of Neko (Google Flow, built from his hoodie photo, brick loft set, mic, open Bible on the table) says the old opening: "Before you walk out that door today ... Pray it with me, and then go." Hook text top-center changes every 1.25 s (BEFORE YOU WALK OUT / THAT DOOR TODAY / PRAY THIS FIRST), then PSALM 91 in gold. First spoken word on frame 1. The picture changes (zoom) at 0.8, 1.6, 2.4 and 3.2 s, then a cut roughly every 7 s. Captions are the same Poppins 110 style.
- 6:46 to 7:31 (6:46.2): the same avatar says the prayer ("So here is the prayer ... I ask it in the name of Jesus Christ, Amen.") and the closer ("Type, amen, and send this to a friend who needs it. Have a blessed day, and remember the word for today."). Then the end card "TYPE AMEN / BLESSED PRAYERS" over footage to 7:37.7.
- The avatar's voice is Neko's own: Flow made the clips with its own voice, and each clip was converted to Neko's voice with Seed-VC (reference: 19 s of Neko). Duration is kept exactly, so the lips stay in time. Numbers (proof-long.md): speaker similarity to Neko 0.80 to 0.88 after conversion (0.46 to 0.60 before); lag against the Flow lips 0 to 10 ms (a frame is 33 ms); pitch and level steady across the 12 clips.
- Two readable aircraft posters on the wall behind him ("AIRBUS A350", "BOEING 747") are blurred out in every avatar shot. I checked frames and OCR; please look at every avatar shot yourself. The "KI" hoodie print is Neko's own Kingdom Impact Shop design and was left in on purpose; its tiny curved line of text is AI-garbled and not readable. Say so if you want it gone.
- Total is now 7:37.7 (457.73 s). The last chapter moved from 6:47 to 6:46. The description gained one line saying the host is an AI-generated version of Neko with his voice. Title, tags and thumbnails are unchanged.
- proof.py: 10 of 10 PASS on the new final (proof-long.md, with the transcript log, the OCR table of every verse page and the avatar numbers).
- If you already answered Round 2, anything you passed on the unchanged middle carries over unless you hear or see something that moved at the seams (item J).

## HISTORY: Round 2 (Nov 27 2026, about 4:30 PM ET), for reference
Your Round 1 result: FAIL on one thing, captions too small for a phone; everything else passed, and you would run thumbnail A. The files in this folder are the new finals. Please answer A to H again (only C needs a full look; the rest a quick confirm that nothing you passed moved):
- BLOCKER, CAPTIONS: now about twice as big (Poppins 58 -> 110), two balanced lines, heavier outline. The top hook text went up with them (104 -> 124). Captions still never sit on a Scripture card.
- YOUR NOTE, the temple: the line now reads "The devil set Jesus on the top of the temple, quoted these very verses, and dared him to jump. Jesus said no." (Matthew 4:5-6). Re-voiced at about 5:28. The video is now 7:39 (459.1 s); the last chapter moved one second (6:47).
- YOUR NOTE, laptop mail screen (0:04 to 0:09 and 2:02): checked on the 1080p master. Full-resolution crops are in laptop_crops.jpg: the screen is out of focus and no logo or word can be read. Say so if you still want the shot gone.
- YOUR NOTE, loudness: the 1080p master measures -14.14 LUFS integrated, true peak -1.32 dBTP (proof-long.md check 2). The 480p review copy now carries the master's own audio stream, copied, not re-encoded.
- YOUR NOTE, "wasteth" at 2:41: voiced WAYST-eth; both speech-to-text models wrote "wasteth". Give it a listen.
- Everything else is the same cut: same footage, same Scripture cards, same thumbnails, same title, description and tags.
- proof.py: 10 of 10 PASS on the new final (proof-long.md, with the transcript log and the OCR table of every verse page).

## What this is
- Blessed Prayers (YouTube). A morning prayer talk through Psalm 91, KJV only. Every work points to Christ.
- LONG only (no Short in this job): 7:37.7 (457.73 s), 16:9, 1080p. Built from IQ Vid's trend pull: Psalm 91 prayer for protection and morning prayer are the two biggest searches in our niche, and "pray this before you step into your day" is the title pattern winning right now.
- Voices: open and close = Neko (AI avatar, his own voice). Teaching in the middle = AI narrator, Kokoro am_michael at 0.92 speed (the long-video standard), unchanged. The description discloses both.
- Picture: avatar open and close; free Pexels stock footage in the middle, matched to each paragraph, no talking faces there. Burned-in captions at the bottom. 
- Scripture is on a SPLIT CARD in the middle: footage left, dark panel with a gold edge right, reference in gold, verse in white serif, key words RED. Long passages turn the page once (Psalm 91:5-8, 91:11-13, 91:14-16 have two pages).
- Ends with a prayer in the name of Jesus Christ, then "Type amen, and send this to a friend who needs it." End card "TYPE AMEN / BLESSED PRAYERS". No prayer requests anywhere.

## Files (480p review copy; the real file is 1080p, same cut, same audio stream)
- long-review-480p.mp4, contact-long.jpg (one frame every 5 s, time stamped), proof-long.md, SEO-long.md, captions.srt, script-long.txt, thumb-A-dont-leave-yet.jpg, thumb-B-pray-this-first.jpg, thumb-C-psalm-91-before-work.jpg, laptop_crops.jpg. All in one folder:
  https://github.com/nekohusser-beep/morning-word-videos./tree/main/tools/starhead-review/psalm91-morning
  Raw file links: https://raw.githubusercontent.com/nekohusser-beep/morning-word-videos./main/tools/starhead-review/psalm91-morning/<file>
- The 1080p master measures -14.11 LUFS integrated, true peak -1.53 dBTP; the 480p copy carries the master's own audio stream, copied, not re-encoded.

## What the machine checks already did (you do NOT redo these, but you may read proof-long.md)
File and format, loudness, black frames, silent gaps, banned phrases, heard-vs-written transcript (medium.en and large-v3 on the finished audio, reconciled, every accepted difference logged in the proof), every Scripture verse spoken word for word against the KJV, every verse page on screen read back by OCR against the KJV, speaker similarity and lip lag for the avatar clips, and IQ Vid's pre-post check (0 to fix). A script cannot see pictures, read small brand text, hear pronunciation or judge whether a face looks right. That is your job.
- Known flags the machines raised, so you are not surprised: one stray "but" heard by one model at 0:55 (verse 2, "my God; in him will I trust"); the other model and a third local pass do not hear it. Please listen. Loudness, black frames and silence are clean.
- The dark stone-arch shot at about 3:45 is dark but not black (the black-frame check passes).

## Footage already pulled by Claude before you saw it (so you know what was looked for)
The dash-cam clip with the amigo canopy and lettered trucks is NOT in this video. Also removed: a laptop shot with a mail logo, a drone shot following a trailer with a logo, a mug with a logo, a night skyline that read as black frames. In Round 3 also removed: the Airbus and Boeing poster text behind the avatar. Please still look at every shot yourself.

## What PASS looks like (every line must hold)
1. The voice speaks the script word for word. No stray syllable, clipped word or doubled word at any join. No wrong pronunciation. Listen for: dwelleth, fowler, noisome, pestilence, buckler, flieth, wasteth, habitation, runneth, "thou hast" (hast as in fast), "where I dwell", honour, shew (said "show"), "Your worry talks all morning long" at about 1:28, and in the avatar parts: "psalm" (the first conversion once turned it into "song"; the redo reads "This Psalm"), "dreading", "cup of coffee", "Jesus Christ, Amen".
2. Captions match what is said, are readable on a phone, are never cut off or covered, and change with the voice.
3. Scripture on screen is identical to the KJV and each page stays up long enough to read at a normal pace. Reference matches the verse. Red key words readable. The page turn does not cut a thought in a bad place.
4. No readable brand, store, truck, sign, license plate or logo in any shot, avatar shots included. No watermark. The Bible with the steel square NEVER appears. (The open Bible on the avatar's table is a plain book.)
5. Each shot fits the line it sits under, nothing odd or AI-glitched, no shot repeated back to back. Known repeats, minutes apart, because the free library is finite: wet road (0:30 area, 1:57, 5:20), clock, fog valley, clouds, cliff mist. Flag any that bother you.
6. The opening: first spoken word on frame 1, opens on the viewer's tension, bold top-center text changing about every 1.25 s, picture changes in the first 4 s.
7. The teaching is faithful to the passage (middle, unchanged): "Four hours are named, the night, the day, the darkness, and noon"; "It never says nothing will come at you. It says you do not have to be afraid of it"; the temple line (Matthew 4:5-7, Luke 4:9-12); "in verse 14 the voice changes. God himself starts to talk." Flag anything doctrinally off or any stock AI phrase.
8. No glorifying the dead, no prayer requests, no tagging or promising future content, no ElevenLabs mention.
9. Ending: the prayer ends "I ask it in the name of Jesus Christ. Amen." The closer is "Type amen, and send this to a friend who needs it. Have a blessed day, and remember the Word for today." Last spoken word at about 7:31.7 (451.75 s), end card to 7:37.7.
10. Loudness feels even: no jump at the seams (0:35 and 6:46), none at the Scripture reads, music never covers the voice.

## Things only you can sign off on (reply with PASS or FAIL on each)
A. Picture, whole video, every shot (brands, signs, plates, odd shots, repeats). In the avatar shots also look at the blurred poster squares on the wall: are they distracting at phone size?
B. Audio (voice, pronunciation, joins, music level). Listen at 0:55 for a stray "but".
C. Captions.
D. Scripture split cards (KJV exact, readable, red words, page turns, time on screen). Unchanged since Round 2.
E. First 8 seconds (hook), now on the avatar.
F. Thumbnails A, B, C: unchanged from Round 2 (no face on them). Claude's pick is A ("DON'T LEAVE YET"). Say which you would run, and whether you want one with the avatar's face instead.
G. SEO-long.md: title A "Dreading Today? Psalm 91 Prayer Before You Walk Out" is true to the video; the new AI-host line is accurate; the four KJV lines are exact; chapter timestamps (0:00, 0:36, 1:36, 2:26, 3:48, 4:40, 5:46, 6:46) each land on the moment the chapter names.
H. Teaching and tone (items 7 and 8).
I. NEW, the avatar as a person on screen (0:00 to 0:35, 6:46 to 7:31). Does the face look like a believable, steady, natural man speaking: no melting, flicker, extra fingers, warped mic or Bible, no teeth or lip glitch, no head jump at a cut, eyes and mouth move naturally? Are the lips in time with the words in every clip? Does it read as the same man in all 12 clips (face, beard, hoodie, hands, set)? Hands rest on the knees and the Bible; flag any frame where they look wrong.
J. NEW, the voice and the seams. Is the avatar's voice one steady voice across all 12 clips (same tone, level and pace), natural, with no robotic or watery sound? Is the seam at 0:35 (avatar to narrator) and at 6:46 (narrator to avatar) acceptable, since the open and close are Neko's voice and the teaching is the narrator's? The voices are different on purpose and the description says so. Say PASS, or what to change (for example, a short line of text or sound at the seams).

## Answer format
One line per item A to J plus a PASS/FAIL for the whole job. For each FAIL: timestamp, what you saw or heard, what the fix should be. Post the answer in this chat. If you cannot open a file, say which one; do not guess.

## Full script (as spoken, Scripture in [[ ]]); the avatar says lines 1-2, the first sentence of line 3 cut at "Psalm 91" and the last two paragraphs
Before you walk out that door today, give me a few minutes. You already know what's out there. The email you've been dreading. The drive. The conversation you keep putting off. And you're about to walk into all of it with nothing between you and the day but a cup of coffee.
This psalm is for the person standing at that door. People have prayed it in hospital hallways, before shifts, and on the way to jobs they were scared to lose. Pray it with me, and then go.
Here is how it starts. Psalm 91, verses 1 and 2.
[[He that dwelleth in the secret place of the most High shall abide under the shadow of the Almighty. I will say of the LORD, He is my refuge and my fortress: my God; in him will I trust.]]
Look at the word dwelleth. That's somebody who lives there. Not a person who stops by when the car breaks down. This one is for an ordinary Tuesday, when nobody is watching and nothing is on fire. When's the last time you prayed before you left the house, instead of after something went wrong?
And look at what the writer does in verse 2. He says it out loud. I will say of the LORD. Your worry talks all morning long. Faith has to talk back.
Verses 3 and 4.
[[Surely he shall deliver thee from the snare of the fowler, and from the noisome pestilence. He shall cover thee with his feathers, and under his wings shalt thou trust: his truth shall be thy shield and buckler.]]
A fowler is a trapper, and a snare is the trap you never saw coming. The bad deal. The wrong crowd. The text you should not have sent. God sees the trap before you ever step toward it.
Then comes the picture I love. Under his wings. A mother bird covers her young with her own body when the weather turns, and whatever is coming has to get through her first.
Verses 5 through 8.
[[Thou shalt not be afraid for the terror by night; nor for the arrow that flieth by day; Nor for the pestilence that walketh in darkness; nor for the destruction that wasteth at noonday. A thousand shall fall at thy side, and ten thousand at thy right hand; but it shall not come nigh thee. Only with thine eyes shalt thou behold and see the reward of the wicked.]]
Four hours are named in there, the night, the day, the darkness, and noon. There is no hour on the clock that was left uncovered. The fear that hits at three in the morning is on that list, and so is the trouble that shows up in broad daylight.
So does that mean nothing bad ever comes near a believer? Read it again. It never says nothing will come at you. It says you do not have to be afraid of it. Jesus said the same thing plainly, in John chapter 16, verse 33.
[[These things I have spoken unto you, that in me ye might have peace. In the world ye shall have tribulation: but be of good cheer; I have overcome the world.]]
Back to the psalm. Verses 9 and 10.
[[Because thou hast made the LORD, which is my refuge, even the most High, thy habitation; There shall no evil befall thee, neither shall any plague come nigh thy dwelling.]]
Thy habitation. It keeps coming back to where you live. Proverbs chapter 18, verse 10 puts it another way.
[[The name of the LORD is a strong tower: the righteous runneth into it, and is safe.]]
Runneth into it. So when the fear comes, run. Say his name. You don't need fancy words. Jesus, help me, is a whole prayer.
Verses 11 through 13.
[[For he shall give his angels charge over thee, to keep thee in all thy ways. They shall bear thee up in their hands, lest thou dash thy foot against a stone. Thou shalt tread upon the lion and adder: the young lion and the dragon shalt thou trample under feet.]]
You have help you can't see. God gives his angels orders about you. How many close calls have you already walked away from? You have probably been kept from things you will never hear about. The truck that did not cross the line. The night you made it home when you had no business making it.
One careful note. The devil set Jesus on the top of the temple, quoted these very verses, and dared him to jump. Jesus said no. This psalm is a shelter for people who walk with God. It was never a permission slip to go looking for danger.
Now listen, because in verse 14 the voice changes. God himself starts to talk. Verses 14 through 16.
[[Because he hath set his love upon me, therefore will I deliver him: I will set him on high, because he hath known my name. He shall call upon me, and I will answer him: I will be with him in trouble; I will deliver him, and honour him. With long life will I satisfy him, and shew him my salvation.]]
Look at the middle of that. I will be with him in trouble. He never said you would not see trouble today. He said you would not be in it alone.
And look at the reason. Because he hath set his love upon me. This whole psalm rests on a relationship, not a formula. If you have drifted, this morning is a good morning to walk back.
So here is the prayer. Pray it out loud if you can.
Father, I am stepping out the door, and I am putting this day under your wing. Cover my house while I am gone. Cover the ones I love, wherever they are right now. When a trap is set, show me before I step. When fear comes, remind me where I dwell. Send your angels ahead of me, and let me come home tonight with a thankful heart. I ask it in the name of Jesus Christ. Amen.
Type amen, and send this to a friend who needs it. Have a blessed day, and remember the Word for today.
