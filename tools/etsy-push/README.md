# etsy-push: our own AnythingMCP for Etsy (built Nov 15 2026)
AnythingMCP's trial (Oct 10-17 2026) gave Claude Etsy API access; it died and reactivation was paid. The one job a browser could never do was attaching the digital PDF. etsy-push does it free on GitHub Actions in this public repo.

| AnythingMCP did | etsy-push does |
|---|---|
| list/get listings, patch, add images | same |
| add the digital file | same (the step Chrome always refused) |
| | `publish` refuses a digital listing with no file (Neko's Nov 6 rule: never made-to-order) |
| | Etsy keys, sign-in and product files all encrypted; nothing sellable readable in this public repo |

Use: `VAULT_KEY=$(cat ../kingdom-brain/tools/etsy/VAULT_KEY.txt) python3 tools/etsy-push/add_file.py <pdf/jpg>` to add a file, write a job into tools/etsy-push/queue/, commit, push. Result in queue/done/. Job formats at the top of etsy_push.py.

One-time setup (Neko): Actions secret VAULT_KEY (value in private kingdom-brain tools/etsy/VAULT_KEY.txt). Then Claude runs mode signin_link, Neko signs in to Etsy and taps Allow, sends Claude the address he lands on (the page errors, that's expected), Claude runs signin_finish. Etsy refresh tokens last 90 days and rotate each run, so any run inside 90 days keeps it alive.
