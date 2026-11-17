# RULE ZERO (read first, every thread, every model)

Never stop after one failed attempt. If a method fails, try the next legitimate method, and keep going through every route (other tools, browsers, repo workflows, other connectors, splitting the job) until the job is done. Report the result, not the reasons it was hard. Say 'I can't' only after every route is tried, and list the routes tried. Applies to every thread and every model: act like Fable. Exception: a safety check or permission block is Neko's decision, not a failed method; say so plainly and give him the options. Neko, Oct 17, 2026.

---

# START HERE (every Claude thread, before anything else)

Neko's single source of truth is `overnight/Claude-Work-Tracker.xlsx`, mirrored as plain text in `overnight/TRACKER.md`.

1. `git pull`, then read `overnight/TRACKER.md` (Tasks, Standing rules, How it was done) before answering where-are-we questions or asking Neko for anything.
2. Never create another sheet or tracker. The ONE exception, set by Neko Oct 17, 2026: Hermes has his own tracker at `hermes/Hermes-Tracker.xlsx` (mirror `hermes/TRACKER.md`); Hermes work goes there. Edit the xlsx only, keep columns, copy row formatting.
3. Every change: set Updated to date and time ET (like `Oct 16 11:50 PM ET`), update Last updated on the Where we are tab, run `python3 tools/tracker_sync.py`, commit, `git pull --rebase`, push, then reply.
4. Stale check: if a row's Updated stamp is newer than what you read, reconcile before changing it.
5. Before saying "I can't", check How it was done, memory /topics/workflow-playbook.md, and overnight/ROADBLOCK-PLAYBOOK.md (ladders per job: work them in order, then report "Routes tried").
6. Answer where-are-we with only what is done and what is not, in a few short lines.

---

Approved Morning Word videos. Test file only.
