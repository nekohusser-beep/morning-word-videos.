"""Boy voice + 'Eli' pronunciation audition (Nov 22 2026). Writes out/boy/*.mp3, out/BOY_PICKS.mp3, out/voices.txt"""
import asyncio, edge_tts, subprocess, os
BOY = "Hi! I'm Eli. Papa, does God hear me, even when I whisper? Dear God, thank You for my Papa. Help me be brave tonight. In Jesus' name, Amen."
V = [
 ("1_ana_lift", "en-US-AnaNeural", "-8%", "-10Hz"),
 ("2_andrew_young", "en-US-AndrewMultilingualNeural", "+0%", "+40Hz"),
 ("3_brian_young", "en-US-BrianMultilingualNeural", "+0%", "+45Hz"),
 ("4_eric_young", "en-US-EricNeural", "+0%", "+45Hz"),
 ("5_steffan_young", "en-US-SteffanNeural", "+0%", "+45Hz"),
 ("6_guy_young", "en-US-GuyNeural", "+0%", "+50Hz"),
 ("7_connor_irish", "en-IE-ConnorNeural", "+0%", "+40Hz"),
 ("8_william_aus", "en-AU-WilliamMultilingualNeural", "+0%", "+40Hz"),
]
ELI = [("eli_A", "Goodnight, Eli. God loves you."), ("eli_B", "Goodnight, Ee-lie. God loves you."),
       ("eli_C", "Goodnight, Eelye. God loves you."), ("eli_D", "Goodnight, E-lie. God loves you.")]
async def main():
    os.makedirs("out/boy", exist_ok=True)
    with open("out/voices.txt", "w") as f:
        for v in await edge_tts.list_voices():
            if v["Locale"].startswith("en-"): f.write(f'{v["ShortName"]}\t{v["Gender"]}\t{",".join(v.get("VoiceTag",{}).get("VoicePersonalities",[]))}\n')
    have = {v["ShortName"] for v in await edge_tts.list_voices()}
    ok = []
    for name, voice, rate, pitch in V:
        if voice not in have: print("missing", voice); continue
        for k in range(3):
            try:
                await edge_tts.Communicate(BOY, voice, rate=rate, pitch=pitch).save(f"out/boy/{name}.mp3"); ok.append((name,)); break
            except Exception as e: print("retry", name, e); await asyncio.sleep(2)
    V[:] = [v for v in V if (v[0],) in ok]
    for name, text in ELI:
        await edge_tts.Communicate(text, "en-US-AndrewMultilingualNeural", rate="-10%", pitch="-6Hz").save(f"out/boy/{name}.mp3")
    parts = []
    for i, v_ in enumerate(V, 1):
        name = v_[0]
        await edge_tts.Communicate(f"Boy {v_[0].split('_')[0]}.", "en-US-JennyNeural").save(f"out/t{i}.mp3"); parts += [f"out/t{i}.mp3", f"out/boy/{name}.mp3"]
    for L, (name, _) in zip("ABCD", ELI):
        await edge_tts.Communicate(f"Papa, name {L}.", "en-US-JennyNeural").save(f"out/t{L}.mp3"); parts += [f"out/t{L}.mp3", f"out/boy/{name}.mp3"]
    open("out/list.txt", "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "out/list.txt", "-ar", "48000", "-ac", "1", "-b:a", "128k", "out/BOY_PICKS.mp3"], check=True)
    for p in parts:
        if "/t" in p and "/boy/" not in p: os.remove(p)
    os.remove("out/list.txt")
asyncio.run(main())
