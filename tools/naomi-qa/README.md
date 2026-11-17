# Naomi clip QA (word-exact check, tail, laugh, gaps, loudness, freeze, voice pitch, look frames)

Run on EVERY clip before it is marked done (workflows/naomi-qa-checklist.md in the private repo).

Setup (once per fresh session, the model is about 600 MB, a few minutes):
    pip install --break-system-packages sherpa-onnx numpy
    mkdir -p tools/naomi-qa/asr && cd tools/naomi-qa/asr
    curl -L -o w.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.en.tar.bz2 && tar xjf w.tar.bz2 && rm w.tar.bz2
(ffmpeg must be installed.)

Use:
    python3 tools/naomi-qa/qa_clip.py <clip.mp4> <line.txt> <voice-ref.mp4>
  <line.txt> holds the locked block text (queue.json "line"). <voice-ref.mp4> is the approved Flow Episode 1 cut (naomi/ref or naomi/clips) for the pitch compare.
  Prints: word match ratio and every diff (must be 1.000; check the last two words), speech span, internal gaps over 0.5 s, tail RMS after the last word (laugh check), LUFS and true peak, freeze/black detection, and saves 3 look frames plus a reference frame (qa_<clip>_*.png) in tools/naomi-qa/ to compare against the episode's outfit image.
  Environment variable NAOMI_QA_DIR changes where asr/ and the output frames live (default: this folder).

    python3 tools/naomi-qa/voicecmp.py <clip-a> <clip-b> [more clips]   # long-term spectrum correlation (voice similarity) between clips
