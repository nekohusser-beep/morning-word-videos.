"""Locked kids cast (Neko Nov 22 2026): Joy=Ana, Mama=Ava, Papa=Andrew, Eli(boy)=Ana lowered. Renders every line of eps/*.json."""
import asyncio, edge_tts, json, glob, os
CAST = {"joy": ("en-US-AnaNeural", "-6%", "+0Hz"), "mama": ("en-US-AvaMultilingualNeural", "-5%", "+0Hz"),
        "papa": ("en-US-AndrewMultilingualNeural", "-10%", "-6Hz"), "eli": ("en-US-AnaNeural", "-3%", "-25Hz")}
async def main():
    for f in sorted(glob.glob("tools/kids-voice-edge/eps/*.json")):
        ep = os.path.basename(f)[:-5]; os.makedirs(f"out/{ep}", exist_ok=True)
        for i, (who, text) in enumerate(json.load(open(f))):
            v, r, p = CAST[who]
            await edge_tts.Communicate(text, v, rate=r, pitch=p).save(f"out/{ep}/{i:02d}_{who}.mp3")
asyncio.run(main())
