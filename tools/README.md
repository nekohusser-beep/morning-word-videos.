# Episode build tools

`psalm-118-24/` is the build of the approved Psalm 118:24 episode (Oct 13, 2026). It is the template for every Morning Word episode.

- `build.py`: the whole edit. Per-line clip table (`CLIP`), picture plan (`VIS`), crossfades into B-roll, cuts with alternating punch-in between camera clips, tone and level matching per line, opener and closer song from the Day 1 master, captions, both output cuts and the .srt.
- `lines.json`: the script, one spoken line per entry.
- `pull.sh`: downloads assets from a draft release (`pull.sh <tag> <dest> <regex>`).
- `captions.srt`: the captions as delivered.

To build a new episode, copy the folder, replace `lines.json`, fill `CLIP` with each clip's speech start and end, and run `python3 build.py`.

## Running without connectors (Oct 2026)
Everything the connectors did now has a free GitHub route. Secrets live in repo Settings > Secrets and variables > Actions.

| Job | Old (connector) | Now (GitHub) | Needs |
|---|---|---|---|
| Schedule / check posts | Buffer connector | `tools/buffer.py` + `buffer.yml` (Buffer's own API, free plan) | secret `BUFFER_API_KEY` |
| Verse cards | Orshot template 24206 | `tools/cards/verse_card.py` (free fonts, PIL) | nothing |
| Narration | ElevenLabs | Kokoro in `sleep-render.yml` | nothing |
| Transcript checks | ElevenLabs transcribe | faster-whisper in `transcribe.yml`, `sleep-qa.yml` | nothing |
| Long YouTube uploads | Buffer | `youtube-upload.yml` (YouTube Data API) | secrets `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` |
| Sleep video master + MP4 | local ffmpeg | `sleep-master.yml` | nothing |
| Sleep reading with animated scenes | ffmpeg | `sleep-scenes.yml` (tools/sleep-scenes/build.py) | nothing |

## Pronunciation guard and re-cuts (Oct 28 2026)
- `stitch/word_risk.py`: `scan script.md` before any credits (flags rare words not proven in `word_ledger.json`), `check script.md transcript.json` after each clip (strict word-for-word diff, risky words heard exactly, non-words fail), `compare a.json b.json` (medium.en vs large-v3 must agree), `seed`. Process: kingdom-brain workflows/pronunciation-guard.md.
- `transcribe.yml` takes `model` (medium.en default, large-v3 for the strict pass); `phonemes.yml` prints the phones actually spoken.
- `stitch/recut.py`: re-cut an old finished master (strip old jingle bookends, trim to speech, loudnorm, add current bumpers). `WORK=dir TP=-1.5 CRF=22 python3 tools/stitch/recut.py [tag...]`; cut points are in `JOBS`.
