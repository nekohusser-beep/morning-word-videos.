#!/bin/bash
# usage: pull.sh <tag> <destdir> [name-regex]
R=nekohusser-beep/morning-word-videos.; tag=$1; dest=$2; re=${3:-.}
RID=$(gh api repos/$R/releases --jq ".[]|select(.tag_name==\"$tag\")|.id" | head -1)
gh api "repos/$R/releases/$RID/assets?per_page=100" --jq '.[]|[.id,.name,.size]|@tsv' | grep -E "$re" | while IFS=$'\t' read id name size; do
  if [ ! -s "$dest/$name" ] || [ "$(stat -c %s "$dest/$name")" != "$size" ]; then gh api -H "Accept: application/octet-stream" "repos/$R/releases/assets/$id" > "$dest/$name"; fi
  echo "$name $size $(stat -c %s "$dest/$name")"
done
