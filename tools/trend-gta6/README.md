# GTA 6 trend Short (Nov 21 2026)
59 s, 1080x1920. Built in a phone thread's cloud workspace, $0.
- Voice: Kokoro am_michael (tts.py, lines.json). Word times: sherpa-onnx parakeet-tdt-0.6b-v2 (align.py). Listening check: sherpa-onnx whisper small.en (listen.py).
- Dark half (dark.py): Pexels stills in src/ (free licence; ids 13341786 hero, 39572247 candles, 18132311 room, 11285597 neon, 27230467 windows), maker's marks on the controller blurred.
- Light half (light.py): our own b-roll at 1080x1920 30 fps in bg/: psalm = tools/ps19-11/broll/br_bible.mp4, eph = tools/isa40-31/broll/br_wheel.mp4 (1.18x slow, minterpolate), home = tools/isa40-31/broll/br_home.mp4 (-ss 0.8), eagle = tools/isa40-31/broll/br_eagle.mp4 (1.3x slow, minterpolate).
- Sound (audio.py): all synthesized in numpy, -14.7 LUFS.
- Facts on screen: ritual Easter egg (Game Rant, Game8, Yahoo Tech), $3.79B first day (Rockstar via Reuters, Nov 20 2026), ESRB M 17+. KJV Psalm 101:3 and Ephesians 5:11 checked with pythonbible.
Order: tts.py, align.py, listen.py, dark.py full, light.py full, audio.py, concat dark+light, mux mix.wav.
