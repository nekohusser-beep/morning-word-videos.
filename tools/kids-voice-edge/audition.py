"""Kids prayer voice audition with Microsoft neural voices (edge-tts, free, no key). Writes out/<name>.mp3 + one combined reel."""
import asyncio, edge_tts, subprocess, os
JOY = "Hi! I'm Joy. ... What's your name? ... Nice to meet you! Let's pray together. Dear God, thank You for this brand new morning. Help me be kind today. In Jesus' name, Amen!"
MAMA = "Good morning, sweetheart! Let's thank God for this brand new day. Fold your hands with me."
PAPA = "Hey there, little man. Before you sleep, let's talk to God together. He's always listening."
BOY = "Hi! I'm Eli. Dear God, thank You for my Papa. Help me be brave tonight. In Jesus' name, Amen!"
V = [
 ("joy_1_ana", "en-US-AnaNeural", JOY, "+0%", "+0Hz"),
 ("joy_2_ana_slow", "en-US-AnaNeural", JOY, "-8%", "+0Hz"),
 ("joy_3_maisie_uk", "en-GB-MaisieNeural", JOY, "-5%", "+0Hz"),
 ("joy_4_ava_young", "en-US-AvaMultilingualNeural", JOY, "-5%", "+25Hz"),
 ("mama_1_ava", "en-US-AvaMultilingualNeural", MAMA, "-5%", "+0Hz"),
 ("mama_2_emma", "en-US-EmmaMultilingualNeural", MAMA, "-5%", "+0Hz"),
 ("mama_3_jenny", "en-US-JennyNeural", MAMA, "-5%", "+0Hz"),
 ("papa_1_andrew", "en-US-AndrewMultilingualNeural", PAPA, "-10%", "-6Hz"),
 ("papa_2_brian", "en-US-BrianMultilingualNeural", PAPA, "-10%", "-6Hz"),
 ("papa_3_christopher", "en-US-ChristopherNeural", PAPA, "-10%", "-4Hz"),
 ("papa_4_roger", "en-US-RogerNeural", PAPA, "-10%", "-4Hz"),
 ("boy_1_ana_low", "en-US-AnaNeural", BOY, "-3%", "-25Hz"),
 ("boy_2_ana_lower", "en-US-AnaNeural", BOY, "-3%", "-40Hz"),
]
async def main():
    os.makedirs("out", exist_ok=True)
    for name, voice, text, rate, pitch in V:
        await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(f"out/{name}.mp3")
        print("ok", name)
asyncio.run(main())
# reel: spoken number tag + sample, so Neko can hear them all in one file
parts = []
for i, (name, *_ ) in enumerate(V, 1):
    tag = f"out/tag{i}.mp3"
    asyncio.run(edge_tts.Communicate(f"Number {i}.", "en-US-GuyNeural").save(tag))
    parts += [tag, f"out/{name}.mp3"]
with open("out/list.txt", "w") as f:
    for p in parts: f.write(f"file '{os.path.abspath(p)}'\n")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "out/list.txt", "-ar", "48000", "-ac", "1", "-b:a", "128k", "out/ALL_VOICES.mp3"], check=True)
