"""KJV Psalm 121, exact words (LORD written Lord so a singer does not shout it). Loaded by lyrics.py when ACE_PSALM=121.
Same case design as the Psalm 23 flow cases: phrase lines, song-style caption, one case per take so the assembler can pick the best sung version of every LINE."""
V = [
    "I will lift up mine eyes unto the hills, from whence cometh my help.",
    "My help cometh from the Lord, which made heaven and earth.",
    "He will not suffer thy foot to be moved: he that keepeth thee will not slumber.",
    "Behold, he that keepeth Israel shall neither slumber nor sleep.",
    "The Lord is thy keeper: the Lord is thy shade upon thy right hand.",
    "The sun shall not smite thee by day, nor the moon by night.",
    "The Lord shall preserve thee from all evil: he shall preserve thy soul.",
    "The Lord shall preserve thy going out and thy coming in from this time forth, and even for evermore.",
]
LINES = [
    ["I will lift up mine eyes unto the hills,", "from whence cometh my help."],
    ["My help cometh from the Lord,", "which made heaven and earth."],
    ["He will not suffer thy foot to be moved:", "he that keepeth thee will not slumber."],
    ["Behold, he that keepeth Israel", "shall neither slumber nor sleep."],
    ["The Lord is thy keeper:", "the Lord is thy shade upon thy right hand."],
    ["The sun shall not smite thee by day,", "nor the moon by night."],
    ["The Lord shall preserve thee from all evil:", "he shall preserve thy soul."],
    ["The Lord shall preserve thy going out and thy coming in", "from this time forth, and even for evermore."],
]
assert [" ".join(x) for x in LINES] == V, "phrase lines must rejoin to the exact KJV verses"
CAPTION_FLOW = ("Gentle flowing sacred folk hymn, one warm male singer, smooth legato melody with continuous phrasing and no long pauses, "
                "each line flows straight into the next, clear English diction, fingerpicked harp and soft acoustic guitar, warm ambient pad, "
                "steady 72 BPM, D minor, calm and comforting, quiet restaurant dinner background music, no drums, no percussion")
CASES = {}
_SETS = {"ffull121": (range(8), 140, "abcd"), "fpA121": (range(0, 4), 64, "abcdef"), "fpB121": (range(4, 8), 72, "abcdef")}
for _name, (_rng, _dur, _ts) in _SETS.items():
    for _t in _ts:
        CASES[f"{_name}_{_t}"] = {"verses": [V[i] for i in _rng], "lines": [LINES[i] for i in _rng], "duration": _dur, "caption": CAPTION_FLOW}
