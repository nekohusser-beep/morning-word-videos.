"""Locked kids cast (Neko Nov 22 2026): Joy=Ana, Mama=Ava, Papa=Andrew, Eli(boy)=Guy +50Hz (Neko pick #6, Nov 22). Renders every line of eps/*.json."""
import asyncio, edge_tts, json, glob, os
CAST = {"joy": ("en-US-AnaNeural", "-6%", "+0Hz"), "mama": ("en-US-AvaMultilingualNeural", "-5%", "+0Hz"),
        "papa": ("en-US-AndrewMultilingualNeural", "-10%", "-6Hz"), "eli": ("en-US-GuyNeural", "+0%", "+50Hz")}
async def main():
    for f in sorted(glob.glob("tools/kids-voice-edge/eps/night*.json")):
        ep = os.path.basename(f)[:-5]; os.makedirs(f"out/{ep}", exist_ok=True)
        for i, row in enumerate(json.load(open(f))):
            who, text = row[0], (row[2] if len(row) > 2 else row[1])
            v, r, p = CAST[who]
            for k in range(4):
                try:
                    await edge_tts.Communicate(text, v, rate=r, pitch=p).save(f"out/{ep}/{i:02d}_{who}.mp3"); break
                except Exception as e:
                    print("retry", ep, i, who, repr(e)); await asyncio.sleep(3)
asyncio.run(main())
