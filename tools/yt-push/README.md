# yt-push: our own Zapier for YouTube (built Nov 15 2026)
Lives in the PUBLIC repo morning-word-videos. because Actions in private kingdom-brain are refused for billing (since Nov 8 2026); public repos run free with no minute cap. No personal data goes in a job.
Zapier's only real job for us was writing YouTube metadata through Neko's Google account (Oct 29 2026: 43 title/tag edits, 2 tasks a call, 100 free tasks, then a paywall). yt-push does that and more, free, no task limit, zero Claude tokens.

| Zapier did | yt-push does |
|---|---|
| titles, tags, descriptions (videos.update) | same, from IQ Vid's content_pack.json or plain fields; full snippet resent so nothing gets wiped |
| nothing else for us | translated titles (only on languages the video already has), playlists, channel comment, caption upload |
| no rollback | old metadata saved to reports/yt-push/rollback/ before every write |
| "done" on faith | re-reads the video after each write; a difference = FAILED |

## Use
1. `python3 tools/yt-push/queue_job.py VIDEO_ID --pack <kingdom-brain or local path>/pack/content_pack.json` (copies title, description, tags and captions into the job) (add `--playlist`, `--comment`, `--captions` as needed).
2. `git add -A && git commit -m "yt-push job" && git push`. The yt-push workflow fires on its own and applies it.
3. Result: tools/yt-push/queue/done/<job>-<time>.json (changed / skipped / errors) and reports/yt-push/run-<id>-apply.txt.
Modes by hand (Actions > yt-push > Run workflow): check, dry, apply, verify, signin.

## Limits (YouTube's, not ours)
- The API cannot pin a comment: the comment posts, the pin is one Studio click.
- Quota: 10,000 units a day free. One video update is about 50 units with its re-read, a caption upload about 400. Roughly 150 full edits a day.

## One-time setup (Neko only: Google credentials)
Secrets YT_CLIENT_ID + YT_CLIENT_SECRET (a "TV and Limited Input devices" OAuth client in the same Google Cloud project as YOUTUBE_API_KEY, blessedprayers4 added as a Test user), then one run with mode `signin` and one tap at google.com/device. The sign-in is saved encrypted in tools/yt-push/signin.enc (key = the client secret, which lives only in Actions secrets). No tap after that.
Note: an External app left in Testing status expires sign-ins after 7 days. Publishing the consent screen to "In production" (no Google review is needed for a single user's own channel; the "unverified app" screen just needs Continue) makes it permanent.
