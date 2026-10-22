#!/usr/bin/env python3
"""Builds scenes_planned.json for Short 3 (instruction gag). The scene cuts follow the joke (half one / half two),
so they are set here by hand; the spoken text is still locked with plan.py's sha and checked word for word:
  python3 make_scenes.py && python3 ../plan.py check scenes_planned.json --script script.txt"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import plan

INSTR, NARR = ("bm_george", 0.92), ("am_michael", 1.0)
# (vo, kind, voice, hold seconds of silent action after the voice, image prompt, motion)
S = [
 ("Okay. Easy one. Grab the salt shaker...", "character", INSTR, 2.2, "Stick figure sits at a kitchen table with a coffee mug, salt shaker and sugar bowl; he grabs the shaker and salts the coffee. Instructor speaker icon top right.", "push_in"),
 ("...and move it so you don't mix it up with the sugar.", "character", INSTR, 1.8, "He is still shaking salt into the mug, then freezes mid-shake with a thought-dots note.", "pull_out"),
 ("Two parts to that sentence. He did one.", "abstract", INSTR, 1.4, "Graphic: a sentence bar split into PART 1 (green, check) and PART 2 (grey); a yellow ball runs part 1 then hops off the bar.", "drift_up"),
 ("No problem. If anything goes in the wrong cup, pick up the spoon...", "character", INSTR, 2.0, "He grabs the spoon the second he hears it and stirs the salty coffee hard; coffee sloshes.", "push_in"),
 ("...and set it down. I'll bring you a fresh one.", "character", INSTR, 2.0, "Still stirring, he freezes with the spoon in the mug; thought-dots note.", "pull_out"),
 ("You got all that?", "character", INSTR, 2.6, "He turns and stares at the camera, eyes wide, one sweat drop, slow blink.", "push_in"),
 ("If you move before the sentence ends, same here.", "abstract", NARR, 0.3, "Graphic: the same sentence bar; this time the ball waits, then runs the whole bar and gets a check.", "pan_right"),
 ("What helps me: let them finish the sentence. Then pick up the spoon.", "character", NARR, 1.0, "Calm figure at the table, hands folded, waits, then picks up the spoon with a fresh cup.", "push_in"),
]
scenes = []
for n, (vo, kind, voice, hold, img, mot) in enumerate(S, 1):
    words = len(vo.split())
    scenes.append({"id": f"s{n:03d}", "vo": vo, "words": words, "est_sec": round(words / 2.7, 2), "kind": kind, "voice": voice[0], "speed": voice[1],
                   "hold": hold, "chars": ["Hero"] if kind == "character" else [], "image_prompt": img,
                   "motion_prompt": "frame-by-frame rig animation (see short_instr/draw.py)", "motion": mot})
d = {"title": "The Instructions", "aspect": "9:16", "wps": 1.9, "max_sec": 8,
     "script_sha": plan.sha([s["vo"] for s in scenes]),
     "base_prompt": "Colored stick figure, red shirt, blue pants, round white head, clean ink outlines, flat bright rooms.",
     "characters": {"Hero": "colored stick figure, red shirt, blue pants"}, "scenes": scenes}
json.dump(d, open(os.path.join(HERE, "scenes_planned.json"), "w"), indent=1, ensure_ascii=False)
print(len(scenes), "scenes,", sum(s["words"] for s in scenes), "words")
