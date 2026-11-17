"""Sound mix for one film. build.py runs this inside the film folder.
Edit the marked block only. Plants and EVENTS come from film.js, so sound stays on the picture's clock."""
import json, os, sys
sys.path.insert(0, os.environ["STICKMAN_SCRIPTS"])
from audio_kit import Mix

info = json.load(open("film.json"))
m = Mix(info["dur"], seed=9)

# ---- EDIT FROM HERE: set this from the sound brief ----
SFX, MUSIC, VOICE = True, True, "vo.mp3"
if SFX:
    m.room_bed([(0, .5), (info["dur"], .45)])
    for e in info["events"]:
        t, k = e["t"], e["k"]
        if k == "hot": m.sfx("impactsoft-medium-000", t, 1.2, 4000, .25, .3)
        elif k == "lift": m.cloth(t, .2)
        elif k == "cold": m.sigh(t + .1, .25)
        elif k == "cupdown": m.cup_down(t, pan=.3)
        elif k == "whoosh": m.whoosh(t, d=.8, g=.3)
        elif k == "tick": m.tick(t, g=.06, pan=.4)
if MUSIC:
    m.music(mood="hopeful", bpm=96)
if VOICE:
    m.voice(VOICE, at=.5)
# ---- TO HERE ----
m.write("audio.wav")
