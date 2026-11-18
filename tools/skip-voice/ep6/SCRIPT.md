# Big Skip Ep (at home) - "I'm Not Hungry"
Neko's script, Nov 17 2026. Characters: SKIP (locked Skip voice, lock/ref_skip.wav), NIA his wife (voice: audition nia-voice-audition.yml, Neko picks).
Dialogue is verbatim in lines.json (25 lines, 12 Nia). Scene -> line map in cfg.json.
FIRST 3 SECONDS: first word on frame 1 (line 0), bold top-center "SHE SAID SHE'S NOT HUNGRY" from frame 1, text swaps every 1-1.5 s, punch-ins on 4/6/10/19/24.
Scenes: 1 kitchen 6:00 PM, 2 car drive-thru, 3 couch 6:40, 4 couch 6:45 (ketchup), 5 dark bedroom 10:00, 6 kitchen 10:05 (second bag from microwave).
End card: "Tag somebody who's 10 o'clock hungry 😂"
Seed: description carries 1 Cor 13:4 KJV ("Charity suffereth long, and is kind").
Blocker: renderer (bigskip_render.py) only has break-room art. Needs 6 new stills (Skip + Nia, same look as ep2b/build/*.jpg) from Flow on Browser 2, then a home renderer cfg.
