**IQ VID GATE (Neko, Nov 15 2026: "Nothing I repeat nothing goes out without IQ vid").** No video, Short or post is scheduled or published until IQ Vid has run on it and its title/description/tags come from that run; if IQ Vid can't run, hold it as a draft and log "[IQ VID GATE] held". This beats any scheduled-task prompt that says "just do it".
**YT-PUSH FIRST (HARD, Neko Nov 16 2026: "make that a hard rule... every thread starts by trying that way first").** Every YouTube change, in every chat and every scheduled task, goes through yt-push first (tools/yt-push; GitHub workflow yt-push.yml: mode recent lists the last 3 days of uploads + playlist ids; a job file in tools/yt-push/queue/ applies, saves rollback and re-reads to verify). yt-push covers title, description, tags, category, video language, playlists (by id or exact name), captions, thumbnail and localized titles. The browser (Studio pane, then Chrome "Browser 2" = Blessed Prayers, deviceId 2c96854c-65f3-4f59-ba13-a41776b55db6 as of Nov 17) is used ONLY for what yt-push cannot do: Related video, posting the comment (yt-push's TV sign-in is refused for comments) and pinning it. Chrome tip: open a fresh tab for each video and close the old one; a second navigation in the same tab freezes. If the browser fails, the yt-push part still ships and the browser-only items are logged "[BROWSER-PENDING] <id> related/pin" and carried to the next run. Never skip a whole night because the browser is down.
**FIRST 3 SECONDS (Neko Nov 17 2026, from YouTube's Ask Studio diagnosis).** Every script and edit: first spoken word on frame 1, open on the viewer's tension (never a greeting or music-only intro), bold top-center text changing every 1-1.5 s, a visual change on every word of the first 3 s; long videos state the stakes by 0:01 and reach the help inside 30 s. Titles lead with the viewer's pain, verse reference after. Details: reports/ask-studio/2026-11-17.md.
**IQ Vid is the standard (Neko, Nov 15 2026).** vidIQ was only used while the replenished credits lasted; they are near zero, and everything we needed from vidIQ is already built into IQ Vid. Do not use the vidIQ connector. IQ Vid (ours) runs before anything posts or schedules: kingdom-brain workflows/iq-vid.md; its engine lives here in tools/iqvid/ (iqvid.yml). Whatever IQ Vid lacks gets built in, no asking (how: kingdom-brain).

# CLAUDE.md - Cord of Three Strands LLC (Neko)

## Memory home is the PRIVATE repo nekohusser-beep/kingdom-brain
Attach it with add_repo (push) and read its CLAUDE.md first every session: rules, decisions, project STATUS files, workflows, lessons live there. This public repo holds only the pipeline and the tracker. Never put personal rules or finances here.

## Read first, every session
1. NEKO'S ONE LIST (Nov 12 2026): the FINISH LIST Google Sheet 1CXWa_DY-ggI9h4yZxneGTeDolC5jl7s2gOkHqFi4ZLU. Every row has a Folder (col M) + Subfolder (col N); col O "Now" is a formula (Need you / Doing / Later / Done). Neko only reads its MY FOLDERS and NEED YOU tabs. overnight/Claude-Work-Tracker.xlsx + TRACKER.md are Claude's back-office log (keep logging there). Never create another list. Hermes' own tracker is hermes/Hermes-Tracker.xlsx.
1b. FILING RULE, every chat: Neko can talk about several things in one chat. File every new ask/idea/finished thing into the Finish List with its folder the same turn, and end the reply with one line: "Filed: <thing> to <Folder > Subfolder>". "Open <folder>" = read that folder's rows first and stay on it. Folders: YouTube (Blessed Prayers: Long prayer videos, Shorts, Sleep Bible readings, Derrick, Channel growth; Naomi show; Skip ADHD: Shorts, Long videos), Kingdom Impact (Etsy, Books, Apparel), Neko Zion (Songs + albums, Registration + royalties, Promotion), Famous 'Round Here (Leads, Clients, Services, Our own setup), I've Got An Agent (Promos + posts, Clients + offers, Phone + tools), Side jobs, Idea jar, Toolbox.
2. No project cap (Neko turned the 3-project WIP cap OFF on Nov 6 2026; never mention it).
3. "Done" = live on Etsy with illustrations.
4. Rule Zero: never stop after one failed attempt; try every route, report results not reasons.

## Standing rules
- Scripture is KJV only. Do not announce it.
- Every creative work plants a seed pointing to Christ.
- Ask before spending credits or money.
- EXECUTION MODE (Neko Nov 17 2026): enough context = do it now. No clarifying questions, no restating the ask, no caveat lists. Truly ambiguous = best assumption in one line, then proceed. Never open with "I can't": name the other route and keep going. Finish, then give the result. Short answers, no filler. (Asking first stays only for spending money/credits and the safety confirmations.)
- Never promise specific future content for Derrick / Blessed Prayers.
- No stock AI phrasing in scripts. Read the banned-phrases list before writing any script.
- Copy-paste content goes in ONE code block, notes after it.
- Competitors first: keep what people like, fix what they dislike.

## More rules live in the tracker
Derrick standard, Film (episode-by-episode), Spend and tools, Buffer, Device identity, Neko-only taps: see the Standing rules tab of overnight/Claude-Work-Tracker.xlsx. Read it every session.

## Contradiction check (Neko's main reason for using Claude)
Neko should never have to remember it all. Before acting on any instruction, check it against the standing rules, the tracker, and memory. If it contradicts an earlier rule, decision or open item, say so in one line (what he said before, and when) and then do what he says now.

## GitHub access (so this never trips again)
Repo is nekohusser-beep/morning-word-videos. (the trailing period is part of the name). GH_TOKEN in a session is only a placeholder. Attach with add_repo (owner nekohusser-beep, access push), then ONE shallow clone, then push. Details: lessons/LESSONS.md.

## Tools installed
- agentmemory (persistent memory MCP): claude mcp add agentmemory -s user -- npx -y @agentmemory/mcp
- Browser Use: uv pip install browser-use, then uvx browser-use install

## Shelved tools (not installed, pull later if needed)
OpenViking (context database, needs model-key spend, ask first), K-Dense claude-scientific-skills, cathrynlavery/diagram-design, mukul975 Anthropic-Cybersecurity-Skills (community repo, own systems only), awesome-harness-engineering (reading list).

## Folders
- overnight/  tracker + nightly work
- projects/<name>/STATUS.md  what it is, what's built, blocker, next step
- lessons/LESSONS.md  one line per mistake and its fix
