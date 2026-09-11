---
name: b3-branch-content-audit
description: Use when asked to compare a Biometry 3.0 service's dev/test/main branches or roll back changes merged today; separates content equality from merge history and prevents no-op reverts.
argument-hint: "[service-repo] [optional rollback date]"
disable-model-invocation: true
user-invocable: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# B3 Branch Content Audit

## When to use

Use for a named `b3-*` service when the user asks what differs between `dev`, `test`, and `main`, asks to synchronize only after evidence, or asks to roll back changes from a specific day.

Do not use this as authority to merge, revert, force-push, or deploy. Those actions need explicit scope and current evidence.

## Inputs / context to gather

1. Confirm the actual source checkout, current branch, remote, and requested branches. B3 project workspace folders may only contain context/results; sources usually live under `/Users/dk/ai/code/beeline/biometry-3.0/<service>`.
2. Record the requested timezone/date if rollback is requested. Use Asia/Almaty bounds and UTC when “today” might be ambiguous.
3. Preserve the worktree branch; comparing remote refs does not require checkout switching.

## Procedure

1. Fetch only the three remote refs explicitly:
   ```sh
   git fetch --prune origin '+refs/heads/dev:refs/remotes/origin/dev' '+refs/heads/test:refs/remotes/origin/test' '+refs/heads/main:refs/remotes/origin/main'
   ```
2. For each pair (`dev:test`, `test:main`, `dev:main`), collect all of:
   - commit ID and `^{tree}` SHA;
   - `git merge-base --is-ancestor` in both relevant directions;
   - `git rev-list --left-right --count origin/<left>...origin/<right>`;
   - `git diff --stat` (and focused diff when trees differ).
3. Report tree/content equality separately from commit/history divergence. Extra merge commits with equal tree SHA are history-only differences.
4. If rollback is requested, fetch `origin/main` again and use date-bounded first-parent history before creating anything:
   ```sh
   git log --first-parent --format='%H%x09%cI%x09%an%x09%s' --since='<YYYY-MM-DD> 00:00:00 +05:00' --until='<YYYY-MM-DD> 23:59:59 +05:00' origin/main
   ```
5. If no qualifying commits exist, report the no-op result and do not revert or push. If commits do exist, stop for authorization unless the user explicitly authorized the exact rollback scope.

## Efficiency plan

1. Use the explicit fetch refspec once; do not rely on stale tracking refs or broad repository scans.
2. Keep one compact comparison table/report with tree SHA, divergence count, ancestry, and diff result.
3. For zsh loops, encode pairs as `dev:test` and use `${spec%%:*}` / `${spec##*:}`; avoid `set -- $pair`.
4. Stop after the four independent checks agree; only open a full file diff when trees differ.

## Pitfalls and fixes

1. Symptom: different commit IDs are reported as different code.
   - Likely cause: history was checked without tree/content comparison.
   - Fix: compare tree SHA and `git diff` before describing code differences.
2. Symptom: `ambiguous argument 'origin/dev test...origin/'` in zsh.
   - Likely cause: branch-pair string split through `set -- $pair`.
   - Fix: use colon-separated pairs and shell parameter expansion.
3. Symptom: a requested “today” rollback would create an empty revert.
   - Likely cause: target branch and timezone-bounded first-parent commits were not proven.
   - Fix: fetch `origin/main`, inspect explicit date bounds, and skip action when no commits qualify.

## Verification checklist

1. Remote `dev`, `test`, and `main` were freshly fetched with explicit refspecs.
2. Every claimed content difference has tree SHA plus diff evidence; every history claim has ancestry/divergence evidence.
3. The working checkout branch was unchanged unless the user explicitly requested a switch.
4. Any rollback request has an explicit target date/timezone and first-parent evidence.
5. No revert or push was made when the qualifying commit set was empty.
