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


def _lyrics_for_v1(case, flow="verse"):
    vs = CASES[case]["verses"]
    if flow == "lines":
        idx = [int(case[1:]) - 1] if re.fullmatch(r"v[1-6]", case) else list(range(len(vs)))
        if len(idx) == 1:
            return "[Verse]\n" + "\n".join(LINES[idx[0]])
        return "\n\n".join(f"[Verse {n + 1}]\n" + "\n".join(LINES[i]) for n, i in enumerate(idx))
    return "\n\n".join(f"[Verse {i + 1}]\n{v}" for i, v in enumerate(vs)) if len(vs) > 1 else f"[Verse]\n{vs[0]}"


def plain_for(case):
    return " ".join(CASES[case]["verses"])


# ---- FLOW cases (Neko Oct 30 2026 1:56 AM ET: "large gaps between the wording ... I need it to sing, to flow, like a restaurant soundtrack") ----
# Same exact KJV words, split into phrase lines so the singer phrases them; song-style caption instead of "chant"; pass length ~1 s per word.
LINES = [
    ["The Lord is my shepherd;", "I shall not want."],
    ["He maketh me to lie down in green pastures:", "he leadeth me beside the still waters."],
    ["He restoreth my soul:", "he leadeth me in the paths of righteousness for his name's sake."],
    ["Yea, though I walk through the valley of the shadow of death,", "I will fear no evil:", "for thou art with me;", "thy rod and thy staff they comfort me."],
    ["Thou preparest a table before me in the presence of mine enemies:", "thou anointest my head with oil;", "my cup runneth over."],
    ["Surely goodness and mercy shall follow me all the days of my life:", "and I will dwell in the house of the Lord for ever."],
]
assert [" ".join(x) for x in LINES] == V, "phrase lines must rejoin to the exact KJV verses"
CAPTION_FLOW = ("Gentle flowing sacred folk hymn, one warm male singer, smooth legato melody with continuous phrasing and no long pauses, "
                "each line flows straight into the next, clear English diction, fingerpicked harp and soft acoustic guitar, warm ambient pad, "
                "steady 72 BPM, D minor, calm and comforting, quiet restaurant dinner background music, no drums, no percussion")
_FLOW = {"ffull120": (range(6), 120), "ffull150": (range(6), 150), "fp1": (range(0, 2), 38), "fp2": (range(2, 4), 62), "fp3": (range(4, 6), 62)}
for _name, (_rng, _dur) in _FLOW.items():
    for _t in "abcd":
        CASES[f"{_name}_{_t}"] = {"verses": [V[i] for i in _rng], "lines": [LINES[i] for i in _rng], "duration": _dur, "caption": CAPTION_FLOW}


def lyrics_for(case, flow="verse"):  # accepts run.py's 2nd arg (ACE_FLOW); flow cases carry their own phrase lines
    c = CASES[case]
    if "lines" in c:
        return "\n\n".join(f"[Verse {i + 1}]\n" + "\n".join(ls) for i, ls in enumerate(c["lines"]))
    return _lyrics_for_v1(case, flow)
