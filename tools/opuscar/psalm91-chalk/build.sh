#!/bin/sh
# Psalm 91, Chalkboard style (lemomo-ai/lemo-opuscar engine). One command from a clone of lemo-opuscar with this folder
# copied to films/psalm91-chalk:  sh films/psalm91-chalk/build.sh
# Needs: Node 20+, ffmpeg 7+ on PATH (static build from github.com/BtbN/FFmpeg-Builds), the core and voice tiers:
#   sh plugin/skills/lemo-opuscar/scripts/setup.sh deps voice
set -e
HERE=$(cd "$(dirname "$0")" && pwd); LIB=${LIB:-$(cd "$HERE/../.." && pwd)}; export LIB
cd "$LIB"; PY="$LIB/.venv/bin/python"
[ -f "$HERE/vo/n1.wav" ] || "$PY" core/tts/tts.py "$HERE/lines.json" "$HERE/vo"      # Kokoro am_michael, KJV lines
node core/render/events.mjs "$HERE"
"$PY" "$HERE/audio.py"
node core/render/video.mjs "$HERE" --fps 30 --workers 3 --out "$HERE/out/video.mp4"
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/mix.wav" "$HERE/psalm91-chalk.mp4" 30 1
echo "done: $HERE/psalm91-chalk.mp4"
