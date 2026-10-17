# START HERE (every Claude thread, before anything else)

Neko's single source of truth is `overnight/Claude-Work-Tracker.xlsx`, mirrored as plain text in `overnight/TRACKER.md`.

1. `git pull`, then read `overnight/TRACKER.md` (Tasks, Standing rules, How it was done) before answering where-are-we questions or asking Neko for anything.
2. Never create another sheet or tracker. Edit the xlsx only, keep columns, copy row formatting.
3. Every change: set Updated to date and time ET (like `Oct 16 11:50 PM ET`), update Last updated on the Where we are tab, run `python3 tools/tracker_sync.py`, commit, `git pull --rebase`, push, then reply.
4. Stale check: if a row's Updated stamp is newer than what you read, reconcile before changing it.
5. Before saying "I can't", check How it was done and memory /topics/workflow-playbook.md.
6. Answer where-are-we with only what is done and what is not, in a few short lines.

---

Approved Morning Word videos. Test file only.
