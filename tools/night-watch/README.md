# Night Watch (Psalm 130:6) build, Nov 16 2026
LTX 4 s clips -> 59.7 s Short, $0. Order: tts.py (Kokoro am_michael 0.94, models from thewh1teagle/kokoro-onnx releases) -> scene.sh N TARGET PINGPONG (ping-pong, setpts stretch >= 1.0 only, minterpolate mci, 1080x1920, grade, grain) -> build.py (voice placement, code-made pad, ASS captions + SRT) -> mix to -14 LUFS -> ffmpeg xfade chain (1.2 s) + subtitles -> lc.py (sherpa-onnx whisper small.en word check, 11/11 lines 1.00).
Scene targets used: S1 11.1 pp, S2 8.2 pp, S3 13.5 pp, S4 6.9 single, S5 8.1 pp, S6 17.9 pp (stretch 1.0-2.24x). Clips: episodes/ltx/nightwatch/*.mp4, S6 = episodes/ltx/ltx23_verse_bg_20261116_0621.mp4.
Paths in the scripts are /tmp/nw (work dir). Video is NOT in this repo: not approved yet.
