import asyncio, edge_tts, os
L = ["Hi!", "I'm Joy.", "What's your name?", "Nice to meet you!", "Let's pray together.", "Fold your hands, and close your eyes.",
     "Dear God,", "thank You for this brand new morning.", "Thank You for my family, and my friends.", "Help me be kind today.", "In Jesus' name,", "Amen!"]
async def main():
    os.makedirs("out", exist_ok=True)
    for i, t in enumerate(L):
        await edge_tts.Communicate(t, "en-US-AnaNeural", rate="-6%").save(f"out/joyline_{i:02d}.mp3")
asyncio.run(main())
