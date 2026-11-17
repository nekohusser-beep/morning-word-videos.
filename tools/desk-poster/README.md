# desk-poster: uploads + schedules from the laptop, as you (built Nov 15 2026)
Replaces the Studio-pane chunk route (MP4 split into 16 MB pieces on GitHub, JS driver re-stitching in the pane, sign-outs killing runs).
GitHub tools checked: wanghaisheng/youtube-auto-upload (ytb-up; Playwright/Selenium + saved cookies, scheduling; last release May 2022, stale) and dreammis/social-auto-upload (~11K stars; Douyin, Bilibili, Xiaohongshu, Kuaishou, TikTok; YouTube "not yet"; cookies once from a real browser, human-like delays). Their method, reverse engineered: a real browser, a saved sign-in, the real upload page, human pace. Ours applies it with the Studio selectors our driver already proved.

- Put `name.mp4` + `name.json` (+ thumbnail) in Desktop\Claude-Work\desk-poster\queue (Claude does this).
- Double-click Run-Uploader.cmd. It installs what it needs, pulls the newest script, uploads every queued video, schedules or publishes, and writes queue\done\name.result.json with the video link.
- First run only: `Run-Uploader.cmd login` (or double-click and sign in when asked) in its own Chrome window; the sign-in is saved in desk-poster\profile.
- Gate: no title/description/tags = refused (IQ Vid gate). A YouTube check flag stops the publish.
- Calibration: the "pick another date" step uses new selectors (time and tomorrow-default are proven); its first run is checked against the screen and the selector fixed if it misses (the script stops rather than scheduling wrong).
- Risk, said once: this drives YouTube's own page like a person would (same as the pane route we already use daily). YouTube's terms prefer its API; keep the pace human, one channel, no mass posting.
Next on the same engine: TikTok (tiktok.com/tiktokstudio/upload), Instagram and Facebook web uploads, which post PUBLIC because they are your own session (no API audit, no Buffer 10-post cap).
