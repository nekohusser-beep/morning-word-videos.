#!/usr/bin/env bash
# Claude side: queue finished videos for the laptop uploader (it pulls release "desk-queue" every 30 min).
# usage: tools/desk-poster/send_to_laptop.sh name.mp4 name.json [thumb.jpg ...]
# Sessions can't upload release assets directly, so: parts on a temp branch -> branch-to-release.yml joins + uploads.
set -e
R=nekohusser-beep/morning-word-videos.
BR="dq-$(date +%Y%m%d-%H%M%S)"
W=$(mktemp -d); mkdir -p "$W/parts"
for f in "$@"; do split -b 95m -d -a 2 "$f" "$W/parts/$(basename "$f").part"; done
git -C "$W" init -q -b "$BR" && git -C "$W" add parts && git -C "$W" -c user.name=claude -c user.email=noreply@anthropic.com commit -q -m "desk-queue $BR"
git -C "$W" push -q "https://github.com/$R" "$BR"
gh api -X POST "repos/$R/actions/workflows/branch-to-release.yml/dispatches" -f ref=main -f "inputs[branch]=$BR" -f "inputs[tag]=desk-queue"
rm -rf "$W"
echo "queued $* via $BR (on the laptop within 30 minutes)"
