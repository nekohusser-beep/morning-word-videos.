#!/usr/bin/env python3
"""youtube.json for a sleep book. Usage: make_meta.py Book "Gospel of Matthew" "The Gospel of Matthew" CHAPTERS HOURS_LABEL OUT.json [bed=waves|none]"""
import sys, json
book, short, full, chapters, hours, out = sys.argv[1:7]
bed = sys.argv[7] if len(sys.argv) > 7 else "waves"
waves_line = "Peaceful crashing waves roll low underneath the whole way through. " if bed == "waves" else "Just the Word, no music underneath. "
title_tail = "Crashing Waves" if bed == "waves" else "Just the Word"
desc = f"""{full} from the King James Version, read slowly and softly for sleep.

All {chapters} chapters, start to finish. No verse numbers, no music swells, no volume spikes. {waves_line}The screen goes dark after the first minute so it won't light up your room, and the reading fades out gently at the end instead of stopping cold.

Made for anyone who wants the Word playing while they rest: night owls, early risers, shift workers sleeping through the day, and anyone whose mind won't settle.

Tip: turn off Autoplay (the switch at the bottom of the player) so nothing else starts when the reading ends. You can also leave it playing on a loop while you are away, so the house is filled with the Word.

Scripture: King James Version (public domain).
Narration: AI-generated voice, produced and mastered by our team.

Books and devotionals from the same ministry, made for people who carry a lot:
Kingdom Impact Shop (Etsy): https://kingdomimpactshop.etsy.com
30-Day Faith Reset Journal for Christians with ADHD: https://www.etsy.com/listing/4504651911/30-day-faith-reset-journal-for
The Debt You're Still Collecting: https://www.etsy.com/listing/4591806225/the-debt-youre-still-collecting
Married Twice: https://www.etsy.com/listing/4590487698/married-twice-first-marriage-to-christ
Can Two Walk Together?: https://www.etsy.com/listing/4577261163/can-two-walk-together-christian-marriage

If this helped you rest, like, subscribe, and share it with someone who has trouble sleeping.

#{book}KJV #KJVBible #SleepWithTheWord #BibleReading #BlessedPrayers"""
sl = short.lower()
tags = [f"{sl} kjv", "bible for sleep", "kjv bible audio", "fall asleep to the bible", "bible reading for sleep", "bible reading for insomnia",
        "bible reading for anxiety", f"{sl} audio", "black screen bible", "peaceful bible reading", "scripture for sleep", "sleep with the word",
        "king james bible audio", "bible audio no music", f"{sl} read aloud"]
json.dump({"title": f"{short} KJV | Soft-Spoken Voice | Dark Screen Bible to Fall Asleep | {title_tail}", "description": desc, "tags": tags, "categoryId": "22", "hours": hours}, open(out, "w"), indent=1)
print("saved", out, len(desc))
