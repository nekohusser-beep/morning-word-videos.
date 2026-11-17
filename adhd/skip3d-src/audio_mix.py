"""Sound mix for one film. build.py runs this inside the film folder.
Edit the marked block only. Plants and EVENTS come from film.js, so sound stays on the picture's clock."""
import json, os, sys
sys.path.insert(0, os.environ["STICKMAN_SCRIPTS"])
from audio_kit import Mix

info = json.load(open("film.json"))
m = Mix(info["dur"], seed=9)

# ---- EDIT FROM HERE: set this from the sound brief ----
SFX, MUSIC, VOICE = True, True, "vo.wav"
if SFX:
    m.room_bed([(0, .5), (info["dur"], .5)])
    for t in info["plants"].get("skip", []):
        m.step(t - .03, g=.2, surface="wood")
    for e in info["events"]:
        t, k = e["t"], e["k"]
        if k == "keys":
            m.sfx("metalclick", t, 1.4, 9000, .25, -.2); m.sfx("impactmetal-light-001", t+.08, 1.6, 9000, .12, -.2)
        elif k == "pat": m.cloth(t, g=.1)
        elif k == "cushion": m.sfx("impactsoft-medium-001", t, 1.0, 4000, .3)
        elif k == "fridge": m.sfx("dooropen-1", t, 1.25, 6000, .3, .4)
        elif k == "fridgeshut": m.sfx("doorclose-1", t, 1.3, 6000, .3, .4)
        elif k == "heart": m.heart(t, g=.5)
        elif k == "bowl": m.sfx("impactglass-light-002", t, 1.1, 8000, .35); m.sfx("metalclick", t+.05, 1.3, 9000, .2)
        elif k == "door": m.door_open(t, pan=-.3)
if MUSIC:
    m.music(mood="hopeful", bpm=96)
if VOICE:
    m.voice(VOICE, at=.6, gain_db=-2.5)
# ---- TO HERE ----
m.write("audio.wav")
