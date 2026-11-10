"""Sound mix for one film. build.py runs this inside the film folder.
Edit the marked block only. Plants and EVENTS come from film.js, so sound stays on the picture's clock."""
import json, os, sys
sys.path.insert(0, os.environ["STICKMAN_SCRIPTS"])
from audio_kit import Mix

info = json.load(open("film.json"))
m = Mix(info["dur"], seed=9)

# ---- EDIT FROM HERE: set this from the sound brief ----
import numpy as np
from audio_kit import SR
SFX, MUSIC, VOICE = True, True, "vo.wav"
def siren(d, f0=620, f1=980, rate=2.2, g=.12):
    t = np.arange(int(SR*d))/SR; f = f0+(f1-f0)*(.5+.5*np.sin(2*np.pi*rate*t))
    ph = 2*np.pi*np.cumsum(f)/SR; s = np.sign(np.sin(ph))*.35+np.sin(ph)*.65
    env = np.minimum(1, t/.05)*np.minimum(1, (d-t)/.2); return s*env*g
def beepkeys(t0, d, rate, g=.09):
    rng = np.random.default_rng(3); k = t0
    while k < t0+d:
        m.nb(k, 2500, 7000, .02, .001, .015, g, rng.uniform(-.3, .3)); k += 1/rate*rng.uniform(.6, 1.4)
if SFX:
    m.room_bed([(0, .35), (8, .35), (8.4, 0), (29.6, 0), (30, .3), (info["dur"], .3)])
    m.air_bed([(0, 0), (8.3, 0), (8.6, .5), (29.4, .5), (29.7, 0), (info["dur"], 0)])
    for t in info["plants"].get("run", []):
        m.step(t-.03, g=.25, surface="wood")
    for e in info["events"]:
        t, k = e["t"], e["k"]
        if k == "type": beepkeys(t, 2.6, 7)
        elif k == "typefast": beepkeys(t, 1.3, 22, .11)
        elif k == "whoosh": m.whoosh(t, d=.8, g=.5)
        elif k == "zip": m.whoosh(t, d=.5, g=.35, pan=.5)
        elif k == "smash":
            m.sfx("impactpunch-heavy-001", t, .9, 6000, .7); m.sfx("impactplate-medium-002", t+.01, .8, 5000, .35)
        elif k == "alarm": m.put(t, siren(2.4), 1, 0, .2)
        elif k == "alarm2": m.put(t, siren(4.4, 700, 1150, 3.2), 1, 0, .2)
        elif k == "pop": m.sfx("impactsoft-medium-002", t, 1.6, 7000, .35); m.sfx("metalclick", t, 1.5, 9000, .2)
        elif k == "ding": m.sfx("impactbell-heavy-002", t, 1.5, 9000, .35)
if MUSIC:
    m.music(mood="hopeful", bpm=104)
if VOICE:
    m.voice(VOICE, at=0, gain_db=-1.5)
# ---- TO HERE ----
m.write("audio.wav")
