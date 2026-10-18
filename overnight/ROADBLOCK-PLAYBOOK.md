# ROADBLOCK PLAYBOOK (reference, not a tracker)

Built Oct 18, 2026 from Neko's last ~20 threads plus a Gemini second opinion, then checked against the tracker and Neko's rules. Read the matching ladder when a job hits a wall, BEFORE saying "I can't". Work the ladder in order. Only after the last route fails say exactly: "Routes tried: [each route and result]." A safety check or permission block is Neko's decision: say so and give him the options.

Sources: VERIFIED = opened this session; FIELD = Neko or a past thread proved it; UNVERIFIED = a lead, test one before relying on it.

## Standing add-ons (from this review)
- Official docs beat this file. If a tool's own docs contradict a line here, report the conflict.
- Neko's ear beats measurements. If a scan passes but he hears a problem, fix it.
- Before any YouTube action, confirm the channel is Blessed Prayers (Studio silently opens whichever account was last active) and log "Channel confirmed".
- Ask for Neko-only steps in one line: "Neko, please [login / payment / secret / file-picker tap / publish tap] on [exact item]. Reply done."
- Claude cannot hear audio. QA is by measurement: speed, pauses, clicks, Whisper word match. Neko judges by ear and gives timestamps; re-render only those segments.

## Ladders

### 1. Derrick video (Flow): voice changes per clip, hiss, skipped clips, garbled numbers, dropped first word, "prominent people" block, credit burn
1. About 15 words per clip, exact spoken line quoted, numbers as words ("the 91st Psalm"), max ~7 clips per batch. Count real clips in the media grid; Flow's chat count lies. Close other Chrome tabs. Project under neko.husser@gmail.com. Lite model, 10 credits per 8 s, ask before spending. (FIELD)
2. Voice: Seed-VC conversion to the approved Psalm 118:24 Derrick audio, then Whisper-verify every line and score with speaker-embedding similarity. (FIELD)
3. Hiss or echo: DeepFilterNet3 on a GitHub Actions runner. (FIELD)
4. Silent visual plus pre-converted audio laid over.
5. HeyGen audio-to-video with the approved Derrick audio (`audio_url` or `audio_asset_id`, MP3/WAV up to 32 MB, `motion_prompt` for gestures) until paid credits end Nov 15; not renewed. (VERIFIED: developers.heygen.com/audio-to-video)
6. Clip Kit for Neko (exact words plus a prompt per clip). Default since Oct 18: Neko runs Derrick clips himself; Claude does kits, QA, stitching.
- Signed Flow URLs expire in about an hour: pull to GitHub immediately.
- A blocked clip: rephrase once, still-image-to-video; failed generations are refunded.
- Stop: two skipped or blocked clips in a batch after rewrites: stop, log credits lost, go to the next route.

### 2. Free whole-face avatar morphs
Abandoned (tested Oct 15-17). Only mouth-only lip-sync or the mic-over-mouth overlay for tests. Then HeyGen audio-to-video, then Clip Kit.

### 3. YouTube multi-hour upload
1. youtube-upload GitHub Action once the 3 secrets exist (YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN). Upload PRIVATE first and check what Studio shows. Docs conflict: Google's videos.insert page opened Oct 18 says unverified projects are NOT forced private and a 1-unit cost in a separate upload bucket; a Gemini-cited mirror said private until audit at 100 units. Test, do not assume. (Parked until Thu Oct 22.)
2. Studio split method: ~90 MB parts to a branch, fetch from raw.githubusercontent.com inside Studio, join, inject. Worked for Psalms. Only raw.githubusercontent.com works (CSP blocks release URLs). (FIELD)
3. Neko picks the file in the native picker.
- The Chrome extension cannot (10 MB limit, YouTube freezes it).

### 4. Buffer
Free plan: 3 channels, 10 queued per channel, video by public URL only (copy the mp4 into repo verse-shorts/ and use the raw.githubusercontent URL). Refill as slots free. Overflow: post direct in the browser. No upgrades without Neko's yes.

### 5. Facebook
Link posts only in the built-in browser (laptop awake, pane visible), about 3 groups a day, read each group's rules, fresh wording, never tag. Etsy links only where rules allow; never in cold outreach. Graph API is a dead end (no Page permissions). A group blocked by a safety check: rewrite once, then skip that group for the day. That block is Neko's call.

### 6. Etsy
Claude fills every listing field in the browser (title, description, tags, price, category, mockups); Neko attaches the PDF and taps publish. If the PDF is missing, make it first. Field-fill fails twice: send one message with the exact missing field and the draft text. Done = live with illustrations.

### 7. Sleep Bible audio and thumbnails
Render, master, QA, glitch scan (workflows in How it was done). Thumbnails: photoreal, modest, soft-spoken woman with a Bible on a beach at dusk; reject cartoonish or immodest before Neko sees it. Description must carry the shop link plus 3-4 book links and "peaceful crashing waves". Discoverability: titles and descriptions match search intent; check vidIQ; funnel from Verse Shorts and nightly cards; judge after about 30 days.

### 8. Nightly verse card
1. `tools/cards/mist_card.py` (built, free). Background from Neko's Gemini Pro plan, vivid, never the Bible app's photos. Narrator circle bottom right.
2. Canva free (check one export for a watermark).
3. Orshot last: free plan is about 100 credits a month, so a nightly card would use about 30; Neko wants those saved for things that matter.
- Verse text copied from a KJV source, never from memory; if reference and text disagree, ask.
- Checks: links return 200, verse matches the source word for word (OCR or manual), right channel avatar.

### 9. Copyright Office and Fiverr
Neko does login, payment, audio upload, final tap. Claude fills every other field; Suno origin disclosed and excluded. Fiverr "Press & Hold" check: do not bypass and do not raise before Tue Oct 20.

### 10. Self-hosting
Mon Oct 19, 9-10 AM ET at the new laptop (tracker T1). One orchestrator (Hermes). Docker only after Hermes runs and reads the tracker. Model spend needs Neko's yes.

### 11. Claude behavior
Read the tracker first. Check past threads and this file before saying something can't be done or rebuilding live work. Do not create a second tracker. One deliverable per message. Ask once, then act.

## SOP contract (every repeatable job)
trigger, inputs, ordered steps, automated checks that prove it worked, exactly one file or message to Neko, where he says yes, where it is logged (tracker row, ET stamp).
Automated checks to use: Whisper word match against the script; speaker-embedding score against the approved reference; file count equals the shot list; public URL returns 200; caption passes the banned-phrases scan; right channel confirmed.
