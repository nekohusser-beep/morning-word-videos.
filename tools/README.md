# Episode build tools

`psalm-118-24/` is the build of the approved Psalm 118:24 episode (Oct 13, 2026). It is the template for every Morning Word episode.

- `build.py`: the whole edit. Per-line clip table (`CLIP`), picture plan (`VIS`), crossfades into B-roll, cuts with alternating punch-in between camera clips, tone and level matching per line, opener and closer song from the Day 1 master, captions, both output cuts and the .srt.
- `lines.json`: the script, one spoken line per entry.
- `pull.sh`: downloads assets from a draft release (`pull.sh <tag> <dest> <regex>`).
- `captions.srt`: the captions as delivered.

To build a new episode, copy the folder, replace `lines.json`, fill `CLIP` with each clip's speech start and end, and run `python3 build.py`.
