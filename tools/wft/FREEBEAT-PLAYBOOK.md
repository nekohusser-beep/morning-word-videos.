# Freebeat music video playbook (learned on Word For Today, Nov 17 2026)

Use this for every Neko Zion / JUNG BLOOD / client music video.

## What failed (don't repeat)
- Agent "Music Video" on the whole song in one run: lips don't match, story drifts.
- Lip Sync Video tool (Pixverse / OmniHuman v2): off-sync or failed.
- Still photos with ffmpeg zoom/pan as B-roll: looks like a slideshow. Neko rejected it. Never use stills as filler.

## What works
1. **Singing lines = Photo Karaoke** (Solo, Custom scene <=230 chars, 768p, 16:9).
   - One clean chest-up photo, one face, nothing over the mouth.
   - Upload ONLY the 15 s cut of the song for that lyric window.
   - Duration preset must equal the clip length (15s preset for a 15 s file), slide trimmer to 0:00, Confirm, price ~179.
   - If it says "session expired", hit Retry on the project page (it re-runs without a new charge).
2. **Everything else = Music Video, Freebeat 2.0, Studio model**, in 20-40 s audio segments (cut exactly from the master so it lines up).
   - Attach 3-5 photos of the artist (best face photo first) + the segment mp3.
   - Prompt: start with "B-roll, never singing, mouth closed." then who/where and the actions in order.
   - The agent pauses at each stage (Your Track, Visual Style, Brief, Reference Images, Scene Planning, Video Clips, Final). Click Continue.
   - **Your Track step defaults to a 10 s window. Drag the right handle of the green window to the end** (or the film is only 10 s), then send "Use the full window, about 6 seconds per shot, cut on the beat."
   - Reference images: pick **Nano Banana Pro** (~368-414 credits) for face likeness.
   - Video clips: **Studio** (86 credits/clip, ~10 s clips) looked real and cinematic. Seedance/MiniMax cost 4-12x more.
   - Approve wording the agent offers only after reading it (e.g. it added "chewing" on a lunch shot; told it no eating, lips still).
   - Raw clips play at fb-video-n3.freebeat.ai/.../task_<id>/video.mp4; read them from the page's <video> elements and pull with the wft-grab workflow (sandbox can't reach Freebeat directly).
3. **Assemble** in ffmpeg: master song under everything, clips placed at their song offsets (verify Photo Karaoke offsets by cross-correlation), first frame = motion, fade out last 3 s, -14 LUFS.

## Costs seen
- Photo Karaoke 15 s: ~179. Music Video 30 s segment (Studio + Nano Banana Pro refs + agent): ~700-900.

## Chrome tips
- Open a fresh tab per project; a second navigation in one tab can freeze it.
- Typing into the prompt box: click it, ctrl+a Delete, type, Escape (autocomplete inserts junk otherwise); verify the text via JS.
