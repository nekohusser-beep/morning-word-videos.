# Psalm 91 morning long: build files (Nov 27 2026)
Split-card Scripture look: footage left, KJV panel right, key words red, long passages turn the page once.
- mk_paras.py -> paras.json, sections.json, script.txt, kjv_source.txt (KJV from pythonbible, brackets stripped)
- voice.py (Kokoro am_michael 0.92, per-sentence wavs + tl.json); redo.py re-voices the paragraphs listed in redo.json
- plan.py (footage per paragraph, with the DO-NOT-USE clip list) ; asm_ps91.py t | <chunks> | audio | join (K=0.9, START=0)
- build_srt_chapters.py -> pack/captions.srt + chapter times ; norm_heard_kjv.py = norm_heard.py + logged KJV-spelling rule
- Footage: Pexels ids in plan.py, fetched with pexels-guess.yml into /home/claude/lib/<id>.mp4
The wavs and the 1080p master are not in the repo (size); rebuild with voice.py, or use the master from the chat.
