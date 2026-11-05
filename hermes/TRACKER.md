# TRACKER (auto-generated mirror of Hermes-Tracker.xlsx; edit the xlsx, never this file)

Last updated: Oct 17 2:25 AM ET

Counts: Done 1, In progress 1, Not started 11, On hold 3

## In progress (1)
- [H3] Setup | Model: DeepSeek chosen per Neko. Confirm the exact model supports tool calling and 64K+ context, check the monthly cost, and set a spend limit | NEXT: Check the model in Hermes config with Neko; any spend needs his yes | WAITING ON: Neko: yes on spend. Key goes only in Hermes config, never in chat | Claude | Oct 17 2:25 AM ET

## Not started (11)
- [H2] Setup | Verify the install: run hermes doctor, then hermes, ask it one small question | NEXT: Mon Oct 19, 9-10 AM ET session | WAITING ON: Neko at the new laptop | Claude | Oct 17 2:25 AM ET
- [H4] Setup | Fallback model so one rate limit does not stall a run (OpenRouter free or NVIDIA NIM free credits) | NEXT: Add fallback_providers to Hermes config after H3 | WAITING ON: H3 | Claude | Oct 17 2:25 AM ET
- [H5] Setup | Keep the laptop awake: Screen and Sleep set to Never, lid close set to Do nothing, plugged in | NEXT: Neko does it at the laptop (steps were given Oct 15) | WAITING ON: Neko at the new laptop | Neko | Oct 17 2:25 AM ET
- [H6] Safety | Install Docker Desktop (WSL2) and set Hermes terminal backend to Docker so its commands run in a sandbox | NEXT: Install after H2 passes | WAITING ON: H2 | Claude | Oct 17 2:25 AM ET
- [H7] Safety | Dedicated-machine rules: no personal logins in any browser Hermes can reach; API server bound to 127.0.0.1 with a long random key; secrets only in Hermes config | NEXT: Set during the Monday session | WAITING ON: H2 | Claude | Oct 17 2:25 AM ET
- [H8] Reach | Telegram gateway so Hermes messages Neko when a task finishes | NEXT: Neko makes the bot in BotFather; token goes in Hermes config only | WAITING ON: Neko: bot token, never in chat | Neko | Oct 17 2:25 AM ET
- [H9] Reach | GitHub login for Hermes on the new laptop (so it can read and push to repos) | NEXT: Neko signs in once | WAITING ON: Neko: login | Neko | Oct 17 2:25 AM ET
- [H10] Gate | Test 1: Hermes reads this tracker and says what is open, with no errors | NEXT: Run after H2 | WAITING ON: H2 | Hermes | Oct 17 2:25 AM ET
- [H11] Gate | Test 2: one small real task end to end (create a text file in a repo and push it) | NEXT: Run after H9 and H10 | WAITING ON: H9, H10 | Hermes | Oct 17 2:25 AM ET
- [H12] Gate | Test 3: a scheduled task runs on its own (daily backup of Hermes memory and skills to a private repo) | NEXT: Run after H11 | WAITING ON: H11 | Hermes | Oct 17 2:25 AM ET
- [H16] Setup | Link the Claude desktop app on the new laptop to the Claude chat so Claude can see it | NEXT: Mon 9 AM: open the chat on the new laptop, choose Link to this computer | WAITING ON: Neko at the new laptop | Neko | Oct 17 2:25 AM ET

## On hold (3)
- [H13] Pipeline | Hermes runs Derrick (Morning Word) end to end | NEXT: Starts only after Tests 1-3 pass | WAITING ON: H10, H11, H12 | Hermes | Oct 17 2:25 AM ET
- [H14] Pipeline | White-hat pass on the finished pipeline: try to break it, list every weakness, fix them | NEXT: After H13 is built | WAITING ON: H13 | Claude | Oct 17 2:25 AM ET
- [H15] Integration | Move Tracker A (Blessed Prayers and the rest) rows into this tracker | NEXT: Only after Hermes is flawless. Neko says when | WAITING ON: Neko: go-ahead | Claude | Oct 17 2:25 AM ET

## Done (1)
- [H1] Setup | Hermes Agent installed on the new laptop (i5-7300U, 16 GB, Windows 10 Pro 22H2) | NEXT: Verify in H2 | WAITING ON: Per Neko Oct 17. Not yet seen by Claude (this chat is linked to the old i3 laptop) | Neko | Oct 17 2:25 AM ET

## Standing rules
- Own tracker :: This file is Hermes' tracker (Tracker B). The Blessed Prayers tracker (overnight/Claude-Work-Tracker.xlsx, Tracker A) stays separate. Neko, Oct 17, 2026: get Hermes running flawless first, then bring Tracker A's items in. No other sheets, docs or trackers for Hermes.
- Gate :: No Derrick or pipeline work until Tests 1, 2 and 3 (H10-H12) pass. Every claim of 'it works' needs the test output.
- Money :: Ask Neko before spending any of his money or credits. Free first. Any model spend needs his yes.
- Secrets :: Passwords, API keys and tokens never go in chat. They live only in Hermes config or repo secrets.
- Safety :: Dedicated machine: no personal logins in browsers Hermes can reach; Hermes commands run in the Docker sandbox once H6 is done.
- Inherited :: Nothing posts anywhere without Neko's yes on that exact file. KJV only for scripture. No 'tomorrow' promises in Derrick content. Never tag people in posts.
- Update habit :: After every piece of work: update Status, Next step and Updated on this sheet, run python3 tools/tracker_sync.py hermes/Hermes-Tracker.xlsx hermes/TRACKER.md, commit and push before replying. Updated holds date AND time in Eastern, like 'Oct 17 2:30 AM ET'; set Last updated on the Where we are tab to the same stamp.
- Stale check :: Before changing a row, read its Updated stamp. If newer than what you last read, git pull and reconcile first. Never overwrite a newer row with older information.
- Integration :: When Neko says Hermes is flawless, copy Tracker A rows here (same columns), mark them moved in Tracker A, and note it under How it was done.

## How it was done
- Set the Hermes model :: Edit ~/.hermes/config.yaml: model: provider and default. Store keys with hermes config set <KEY_NAME> <value> (Neko types the key himself). Check with hermes doctor, start with hermes, switch provider with hermes model. :: Reference from the pinggy.io Hermes guide. NOT yet run on this laptop.
- Free model route (fallback) :: OpenRouter free models: 20 requests/min, 50/day with no credits, 1,000/day after a one-time $10 credit purchase. Model must support tool calling and 64K+ context. Free model IDs change, so list fresh before choosing. :: Research Oct 16-17. NVIDIA NIM gives free credits (about 40 req/min) as another fallback.
- Sandbox :: Hermes can run shell commands on the machine. Use the Docker terminal backend for any model not yet trusted. :: Needs Docker Desktop with WSL2 (supported on Windows 10 22H2).
