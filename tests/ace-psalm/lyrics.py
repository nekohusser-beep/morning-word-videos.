"""KJV Psalm 23, exact words (LORD written Lord so a singer does not shout it). Two cases for the ACE-Step test."""
import re
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
# One verse per generation (the 6-verse pass skipped, repeated and dropped lines): duration scales with word count.
for _i, _v in enumerate(V, 1):
    CASES[f"v{_i}"] = {"verses": [_v], "duration": max(20, round(len(_v.split()) * 1.6 + 8))}


# Oct 30 (reflow test): SAME exact words, only the LINE BREAKS change. ACE-Step's own docs/en/Tutorial.md says 6-10 syllables per line,
# and Scenario's ACE-Step 1.5 guide agrees; the KJV verse lines run 14-24 syllables. Words are asserted identical below.
LINES = [
    ["The Lord is my shepherd; I shall not want."],
    ["He maketh me to lie down", "in green pastures: he leadeth me", "beside the still waters."],
    ["He restoreth my soul:", "he leadeth me in the paths", "of righteousness for his name's sake."],
    ["Yea, though I walk through the valley", "of the shadow of death,", "I will fear no evil:", "for thou art with me;",
     "thy rod and thy staff they comfort me."],
    ["Thou preparest a table before me", "in the presence of mine enemies:", "thou anointest my head with oil;", "my cup runneth over."],
    ["Surely goodness and mercy", "shall follow me all the days of my life:", "and I will dwell in the house", "of the Lord for ever."],
]
for _v, _l in zip(V, LINES):
    assert " ".join(_l).split() == _v.split(), (_v, _l)


def lyrics_for(case, flow="verse"):
    vs = CASES[case]["verses"]
    if flow == "lines":
        idx = [int(case[1:]) - 1] if re.fullmatch(r"v[1-6]", case) else list(range(len(vs)))
        if len(idx) == 1:
            return "[Verse]\n" + "\n".join(LINES[idx[0]])
        return "\n\n".join(f"[Verse {n + 1}]\n" + "\n".join(LINES[i]) for n, i in enumerate(idx))
    return "\n\n".join(f"[Verse {i + 1}]\n{v}" for i, v in enumerate(vs)) if len(vs) > 1 else f"[Verse]\n{vs[0]}"


def plain_for(case):
    return " ".join(CASES[case]["verses"])
