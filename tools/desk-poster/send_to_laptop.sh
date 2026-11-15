#!/usr/bin/env bash
# Claude side: queue a finished video for the laptop uploader.
# usage: send_to_laptop.sh name.mp4 name.json [thumb.jpg]   (json = IQ Vid title/description/tags + when/playlist)
set -e
R=nekohusser-beep/morning-word-videos.
gh release view desk-queue -R "$R" >/dev/null 2>&1 || gh release create desk-queue -R "$R" --title "desk-poster queue" --notes "Jobs the laptop uploader pulls (desk-poster). Do not delete." --prerelease
gh release upload desk-queue -R "$R" "$@" --clobber
echo "queued: $*  (the laptop picks it up within 30 minutes)"
