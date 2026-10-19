# LESSONS (one line per mistake and its fix)
- Oct 19: "GitHub not working" was not an outage. gh failed because GH_TOKEN in a session is a 14-character placeholder, and the repo was not attached. Fix: call add_repo (owner nekohusser-beep, repo morning-word-videos. with the trailing period, access push), then one shallow clone, then push. Public repos clone without any token.
