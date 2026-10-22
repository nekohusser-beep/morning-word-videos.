# Scene Engine: script to animated video (Oct 22, 2026)
Adapted from the "Stickman Animation Engine" breakdown. Free route first; nothing here spends credits. Workflow and rules: kingdom-brain/workflows/scene-engine.md (private).

| Step | What it does | Our tool |
|---|---|---|
| 1 Topic + title | study proven channels, write original ideas | prompts/1_topic_title.txt in Gemini (exact video URLs; name search fails) |
| 2 Script | pacing and hook from top 5 videos, ~1,000 words, KJV, no banned phrases | prompts/2_script_writer.txt, then Neko approves the exact script |
| 3 Visual plan | scenes of 8 s max, base prompt, image + motion prompt, 20% abstract | `plan.py split` (code, fixes the spoken text) then prompts/3_visual_planner.txt fills pictures, `plan.py check` gates it |
| 4 Assets | one picture per scene, voice per scene | Gemini image app x1 (free Pro), Kokoro voice (free); stills get ffmpeg motion; Gemini/Flow clips only with Neko's yes |
| 5 Edit | voice as skeleton, hard cuts, captions, -14 LUFS | `build.py` (CapCut optional: import timeline.csv as the map) |

```
python3 plan.py split script.txt scenes.json --title "..." --aspect 16:9
# fill pictures + motion (prompt 3), save as scenes_planned.json
python3 plan.py check scenes_planned.json --script script.txt   # must print 0 errors
python3 plan.py prompts scenes_planned.json prompts_out         # one full image prompt per scene
python3 build.py scenes_planned.json assets/ out/ --voice af_nicole [--dry-run] [--music bed.mp3]
```
assets/ holds s001.png (or .mp4) ... one per scene id, optional vo/s001.wav. Kokoro setup: see .github/workflows/sleep-render.yml. GitHub route: workflow `scene-engine`.
Before posting: Neko's yes on the exact file, AI-disclosure flag on every platform, transcript check of the audio against the script. Dry run (`--dry-run`) makes placeholder pictures and tone voice to test the pipeline.
