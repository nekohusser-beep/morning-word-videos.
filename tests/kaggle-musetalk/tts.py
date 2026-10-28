# Kokoro voice for the test: one sentence per call, 250 ms of silence between, fixed voice and speed.
import sys, numpy as np, soundfile as sf
from kokoro import KPipeline
voice = sys.argv[1] if len(sys.argv) > 1 else "am_michael"
speed = float(sys.argv[2]) if len(sys.argv) > 2 else 0.92
lines = [l.strip() for l in open("script.txt", encoding="utf-8") if l.strip()]
pipe = KPipeline(lang_code="a")
parts = []
for line in lines:
    for _, _, audio in pipe(line, voice=voice, speed=speed):
        a = audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio)
        parts.append(a.astype(np.float32))
    parts.append(np.zeros(int(0.25 * 24000), dtype=np.float32))
wav = np.concatenate(parts)
sf.write("voice.wav", wav, 24000)
print("VOICE_SECONDS", round(len(wav) / 24000, 2), "voice", voice, "speed", speed)
