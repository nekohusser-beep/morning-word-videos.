# sleep-story: free pipeline for one narrated Bible story with an animated night scene

Built Oct 28 2026 for the Sleep Bible pilot "Who Really Spoke to Pharaoh?" (8:08). Zero credits: numpy/PIL, Kokoro (local), ffmpeg, Whisper via the transcribe workflow.

Work in one scratch folder SP that holds: script.txt, pilot/ (kokoro-v1.0.onnx, voices-v1.0.bin, KJV JSON for each book used, from aruljohn/Bible-kjv).

script.txt format: `T: ` spoken title, plain lines = narration, `» ` lines = KJV quote (exact substring of a verse), blank line = paragraph pause.

Steps (each takes SP as its argument unless noted):
1. `python3 verify_script.py SP`   every » line must be a verbatim KJV substring (0 unmatched).
2. scene: `python3 render_scene.py test SP/frames` to look at frames, then two halves in parallel:
   `python3 render_scene.py part 0 360 SP/loop/a.mp4` and `python3 render_scene.py part 360 720 SP/loop/b.mp4`, concat with ffmpeg -c copy into loop30.mp4 (30 s seamless loop, about 1 s per frame per core).
3. `python3 render_voice.py SP` makes voice.wav + timings.json (af_sarah, speed 0.82, pauses 1.25 s line / 2.7 s paragraph).
4. `python3 build_captions.py SP` makes captions.ass (Poppins; libass draws Poppins at about half the stated size, so Narr/Quote are 68 and Title 168 at 1080p).
5. `python3 build_mix.py SP` adds a quiet generated pad (25 dB under the voice) and writes mix.wav.
6. Encode: loop the 30 s scene with -stream_loop -1, `eq=brightness='-0.045*t/488':eval=frame,ass=captions.ass:fontsdir=...,fade in/out`, audio `loudnorm=I=-16:TP=-1.5:LRA=7` plus fades, libx264 -preset fast -crf 19, AAC 160k.
7. Pronunciation proof: compressed voice.wav on a temp branch, dispatch transcribe.yml (medium.en), diff against the script. Respell only the words it flags (liveth -> livith) and splice just that line with fix_line.py so timings and captions stay in sync.
8. `python3 make_thumb.py SP` makes thumbnail.jpg (1280x720) from the scene.

Do not post: Neko approves the MP4 and thumbnail and sets Public himself.
