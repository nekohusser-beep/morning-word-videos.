#!/bin/bash
# Release helper that works with draft releases (talks to the REST API by release id).
#   rel.sh id TAG                 -> prints release id ("" if none)
#   rel.sh ensure TAG [public]    -> prints id, creating the release (draft unless "public")
#   rel.sh down TAG DIR [REGEX]   -> downloads matching assets
#   rel.sh up TAG FILE...         -> uploads files, replacing same-name assets
set -euo pipefail
R=${GITHUB_REPOSITORY:-nekohusser-beep/morning-word-videos.}
cmd=$1; tag=$2; shift 2
rid() {
  for t in 1 2 3 4 5 6; do
    id=$(gh api "repos/$R/releases?per_page=100" --jq ".[]|select(.tag_name==\"$tag\")|.id" | head -1)
    [ -n "$id" ] && { echo "$id"; return; }
    sleep $((t * 5))
  done
}
case $cmd in
  id) rid ;;
  ensure)
    id=$(rid)
    if [ -z "$id" ]; then
      if [ "${1:-}" = public ]; then
        id=$(gh api "repos/$R/releases" -f tag_name="$tag" -f name="$tag" -f target_commitish=main -F prerelease=true --jq .id)
      else
        id=$(gh api "repos/$R/releases" -f tag_name="$tag" -f name="$tag" -F draft=true --jq .id)
      fi
    fi
    echo "$id" ;;
  down)
    dir=$1; re=${2:-.}; mkdir -p "$dir"; id=$(rid)
    gh api --paginate "repos/$R/releases/$id/assets?per_page=100" --jq '.[]|[.id,.name,.size]|@tsv' | grep -E "$re" |
    while IFS=$'\t' read aid name size; do
      for t in 1 2 3 4 5; do
        gh api -H "Accept: application/octet-stream" "repos/$R/releases/assets/$aid" > "$dir/$name" && [ "$(stat -c %s "$dir/$name")" = "$size" ] && break
        sleep $((t * 10))
      done
      [ "$(stat -c %s "$dir/$name")" = "$size" ] || { echo "download failed: $name" >&2; exit 1; }
    done ;;
  up)
    id=$(rid); [ -n "$id" ] || { echo "no release $tag" >&2; exit 1; }
    for f in "$@"; do
      n=$(basename "$f")
      old=$(gh api --paginate "repos/$R/releases/$id/assets?per_page=100" --jq ".[]|select(.name==\"$n\")|.id")
      [ -n "$old" ] && gh api -X DELETE "repos/$R/releases/assets/$old"
      for t in 1 2 3 4 5; do
        curl -sSf -X POST -H "Authorization: Bearer $GH_TOKEN" -H "Content-Type: application/octet-stream" \
          --data-binary @"$f" "https://uploads.github.com/repos/$R/releases/$id/assets?name=$n" -o /dev/null && break
        sleep $((t * 15))
      done || { echo "upload failed: $n" >&2; exit 1; }
      echo "uploaded $n"
    done ;;
esac
