import re
def spoken(s, engine="generic"):
    s = s.replace("’", "'")
    s = s.replace("LORD", "Lord")
    s = re.sub(r"\bfourscore\b", "four score", s)
    if engine == "kokoro":
        s = re.sub(r"\bliveth\b", "livith", s)      # Kokoro reads liveth as lie-v-th
    return s
