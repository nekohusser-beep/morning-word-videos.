"""KJV Psalm 23, exact words (LORD written Lord so a singer does not shout it). Two cases for the ACE-Step test."""
V = [
    "The Lord is my shepherd; I shall not want.",
    "He maketh me to lie down in green pastures: he leadeth me beside the still waters.",
    "He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake.",
    "Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me; thy rod and thy staff they comfort me.",
    "Thou preparest a table before me in the presence of mine enemies: thou anointest my head with oil; my cup runneth over.",
    "Surely goodness and mercy shall follow me all the days of my life: and I will dwell in the house of the Lord for ever.",
]
CAPTION = ("Slow reverent chanted solo male voice, warm and gentle, clear American English diction, every word sung clearly, "
           "ancient harp and lyre with soft arpeggios, calm ambient pad, 60 BPM, D minor, no drums, no percussion, "
           "sleep-friendly, meditative, reverb")
CASES = {
    "short": {"verses": V[:3], "duration": 75},
    "full": {"verses": V, "duration": 150},
}


def lyrics_for(case):
    vs = CASES[case]["verses"]
    return "\n\n".join(f"[Verse {i + 1}]\n{v}" for i, v in enumerate(vs))


def plain_for(case):
    return " ".join(CASES[case]["verses"])
