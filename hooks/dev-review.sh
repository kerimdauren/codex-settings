#!/usr/bin/env bash
set -euo pipefail

LOCK_FILE="/tmp/claude-dev-review.lock"

if [[ -f "$LOCK_FILE" ]]; then
    exit 0
fi

input=$(cat)
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
[[ -z "$cwd" ]] && cwd="$PWD"

cd "$cwd" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

status=$(git status --short 2>/dev/null || true)
[[ -z "$status" ]] && exit 0

diff_tracked=$(git diff HEAD 2>/dev/null || true)

untracked_files=$(git ls-files --others --exclude-standard 2>/dev/null || true)
diff_untracked=""
if [[ -n "$untracked_files" ]]; then
    while IFS= read -r f; do
        [[ -z "$f" ]] && continue
        size=$(wc -c <"$f" 2>/dev/null || echo 0)
        if [[ "$size" -lt 200000 ]] && file --mime "$f" 2>/dev/null | grep -q "charset=us-ascii\|charset=utf-8"; then
            diff_untracked+=$'\n=== NEW FILE: '"$f"$' ===\n'
            diff_untracked+=$(cat "$f")
        fi
    done <<<"$untracked_files"
fi

full_diff="$diff_tracked$diff_untracked"
[[ -z "$full_diff" ]] && exit 0

claude_md=""
[[ -f "$cwd/CLAUDE.md" ]] && claude_md=$(cat "$cwd/CLAUDE.md")

prompt=$(cat <<'EOF'
Review local git changes against project conventions.

Output format: one line per finding:
`path:line: <severity>: <problem>. <fix>.`

Severity:
- BUG: crash, wrong logic, security issue, race
- STYLE: violation of CLAUDE.md conventions (naming, logging, types)
- ARCH: layer/pattern violation, dependency wrong direction

Skip: praise, restating diff, auto-fixable formatting.
If no issues: output exactly `OK: no findings`.
Output nothing else, no preamble, no markdown headers.

=== CLAUDE.md ===
{{CLAUDE_MD}}

=== DIFF ===
{{DIFF}}
EOF
)

prompt="${prompt//\{\{CLAUDE_MD\}\}/$claude_md}"
prompt="${prompt//\{\{DIFF\}\}/$full_diff}"

touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

review=$(printf '%s' "$prompt" | claude -p --model claude-haiku-4-5-20251001 --max-turns 1 --disallowedTools "Bash Edit Write" 2>/dev/null || true)

[[ -z "$review" ]] && exit 0

summary=$'Auto code review:\n\n'"$review"
jq -nc --arg msg "$summary" '{systemMessage: $msg}'
