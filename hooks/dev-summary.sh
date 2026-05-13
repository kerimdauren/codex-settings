#!/usr/bin/env bash
set -euo pipefail

input=$(cat)
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
[[ -z "$cwd" ]] && cwd="$PWD"

cd "$cwd" 2>/dev/null || exit 0

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

status=$(git status --short 2>/dev/null || true)
[[ -z "$status" ]] && exit 0

stat=$(git diff --stat HEAD 2>/dev/null | tail -n 50 || true)
untracked=$(git ls-files --others --exclude-standard 2>/dev/null | head -n 50 || true)

summary=$'Dev summary:\n'
summary+=$'\nStatus:\n'"$status"
[[ -n "$stat" ]] && summary+=$'\n\nDiff stat:\n'"$stat"
[[ -n "$untracked" ]] && summary+=$'\n\nUntracked:\n'"$untracked"

jq -nc --arg msg "$summary" '{systemMessage: $msg}'
