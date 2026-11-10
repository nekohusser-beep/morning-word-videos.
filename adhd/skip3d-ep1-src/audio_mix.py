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
def siren(d, f0=700, f1=1150, rate=3.2, g=.12):
    t = np.arange(int(SR*d))/SR; f = f0+(f1-f0)*(.5+.5*np.sin(2*np.pi*rate*t))
    ph = 2*np.pi*np.cumsum(f)/SR; s = np.sign(np.sin(ph))*.35+np.sin(ph)*.65
    env = np.minimum(1, t/.05)*np.minimum(1, (d-t)/.2); return s*env*g
def tone(f, d, g=.1):
    t = np.arange(int(SR*d))/SR; return np.sin(2*np.pi*f*t)*np.exp(-t*6)*g
HQ = [(7.5,13.5),(18.5,22),(27,31.2),(36.4,40)]
if SFX:
    k = [(0,.35)]
    for a,b in HQ: k += [(a-.05,.35),(a,0),(b,0),(b+.05,.35)]
    k += [(info["dur"],.35)]; m.room_bed(k)
    ka = [(0,0)]
    for a,b in HQ: ka += [(a-.05,0),(a,.5),(b,.5),(b+.05,0)]
    ka += [(info["dur"],0)]; m.air_bed(ka)
    for t in info["plants"].get("walk", []): m.step(t-.03, g=.22, surface="wood")
    for t in info["plants"].get("run", []): m.step(t-.03, g=.25, surface="wood")
    for t in info["plants"].get("sprint", []): m.step(t-.03, g=.35, surface="wood")
    for e in info["events"]:
        t, kk = e["t"], e["k"]
        if kk == "flop": m.sfx("impactsoft-heavy-001", t, .8, 3000, .6); m.sigh(t+.25, g=.25)
        elif kk == "flop2": m.sfx("impactsoft-medium-002", t, .9, 3000, .45)
        elif kk == "creak": m.sfx("creak1", t, 1.1, 5000, .3)
        elif kk == "whoosh": m.whoosh(t, d=.4, g=.35)
        elif kk == "beep": m.put(t, tone(880, .25), 1); m.put(t+.3, tone(660, .3), 1)
        elif kk == "alarm": m.put(t, siren(4.2), 1, 0, .2)
        elif kk == "launch": m.whoosh(t, d=.6, g=.55); m.sfx("impactsoft-heavy-003", t, 1.2, 4000, .4)
        elif kk == "plug": m.sfx("metalclick", t, 1.0, 8000, .4)
        elif kk == "chime": m.put(t, tone(1046, .5, .08), 1); m.put(t+.12, tone(1568, .6, .08), 1)
if MUSIC:
    m.music(mood="hopeful", bpm=100)
if VOICE:
    m.voice(VOICE, at=0, gain_db=-1.5)
# ---- TO HERE ----
m.write("audio.wav")
