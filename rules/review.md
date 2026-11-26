# Review rules

## When independent review is required

1. **Local code changes.** After finishing the changes in a Git repository and before any commit or push, review the complete task diff, including staged and unstaged changes and task-owned untracked files.
2. **Implementation plans.** Review before presenting a plan for approval, including plan mode or a plan the user asked for. A short progress checklist needs no review.
3. **MR or PR creation.** Review the whole branch against its target before creating the MR or PR. Follow the branch verification procedure below.
4. **Someone else's MR, PR or branch.** When asked in chat to review it, use Claude as a second opinion alongside your own review. Check out the branch in a separate `git worktree` to preserve the user's working tree.
5. **Incident diagnosis.** Have Claude check the proposed root cause against the evidence before presenting it, proposing a fix based on it, or making the fix.
6. **Instruction and configuration edits.** Review changes to `AGENTS.md`, `CLAUDE.md`, rules, skills, configuration or hooks, including files outside Git.
7. **High-risk operations.** Complete independent review before executing production database changes, changes to access permissions, bulk operations, or other work with significant impact or limited rollback options. Review the exact commands or change set, target environment and scope, expected impact, verification steps, and rollback or recovery plan. Reuse an earlier result only if it covered all of these for the operation to be executed. Review again before execution if the commands, change set, or any other reviewed detail changes materially.

In `codex review` or a `codex exec` invocation started with a review request, review the supplied material yourself without launching another reviewer. A nested reviewer call can create a loop when Claude Code invokes Codex. The independent review requirement for high-risk execution still applies.

## Prepare the review input

- State the scope and give the reviewer enough surrounding context to assess the behavior. Include line-numbered evidence where useful. Exclude secrets and unrelated changes, and follow project restrictions on sending material to a reviewer.
- For local changes, include the scoped staged diff (`git diff --cached`), the scoped unstaged diff (`git diff`), and the paths and contents of task-owned untracked files. Use task-owned paths or hunks and include relevant callers, contracts or tests when the diff alone is insufficient. For a branch use the pinned SHA comparison below, and for a single commit use `git show <SHA>`.
- For code, include relevant check results if available. In the review input, ask for concrete failure scenarios in the real flow, including effects on existing callers and data, partial failures, retries, and typical load where they matter. Each finding should explain the trigger, impact, location, and a possible fix. A test gap should identify a regression the current checks would miss.
- For a plan, include the plan and its constraints. In the review input, ask the reviewer to check how each step's success will be verified and how the plan handles relevant partial failures and recovery. For an incident diagnosis, include the proposed conclusion and supporting evidence. For instructions, include the before/after text and any connected requirements needed to check whether the change preserves them. For a high-risk operation, include all the material required by case 7.
- Provide any missing context Claude identifies before accepting the review.

## Run the reviewer

Use Claude Code CLI with `claude-fable-5-2`, effort `medium`, through the Claude subscription. Run `claude auth status` from the temporary review directory outside Git and confirm subscription authentication. Check that API credentials or alternate provider settings do not override it. Never launch Codex to review its own work.

Save the prepared input at an absolute path in `review_input`. From the review directory, run:

```sh
claude -p --safe-mode --strict-mcp-config --tools '' --no-session-persistence \
  --model claude-fable-5-2 --effort medium \
  'Review the supplied material. Report concrete problems only, each with file:line where applicable and a fix. Flag missing context that prevents review.' \
  < "$review_input"
```

The reviewer works from stdin with tools disabled. Wait for its result before passing the review gate. Allow up to 15 minutes and treat a timeout as an unavailable result.

If Claude CLI is unavailable, report why. This includes a missing command, unavailable login, a usage limit, unavailable model, timeout, or an error without a result. Pause high-risk execution until independent review is complete. For other work, use `ponytail:ponytail-review` to review code diffs yourself and do a critical self-review for plans, diagnoses and instruction edits.

## Keep the reviewed material pinned

- For Git work, record `git status --porcelain -uall` before and after each review. For local changes, hash the scoped staged and unstaged diffs separately and record the paths and hashes of task-owned untracked files before and after review. For files outside Git, record their hashes before and after review.
- If a hunk-scoped hash changes, compare the reviewed hunks by content to account for unrelated edits in the same file. Continue through unrelated workspace changes. If the reviewed material changes during review, stop and tell the user.
- Keep the reviewed patches and file contents available for commit and push verification.

### Before committing or pushing

- Before committing, compare `git diff --cached` against the reviewed staged changes and any reviewed unstaged changes or task-owned untracked files now staged.
- Before pushing, verify that all outgoing commits are covered by completed reviews. Compare against the fetched destination tip, or the intended base for an unpublished branch. Keep unrelated changes out of the commit and push.
- Staging already reviewed content needs no new review. A completed review covers commit and push while the outgoing content matches the reviewed changes. Reuse the result while the relevant material remains the same and there is no new finding.

### Before opening an MR or PR

1. Fetch the target branch. Record its tip SHA and the intended source tip SHA. Review `git diff <target-sha>...<source-sha>`.
2. Recheck both tips after review. Immediately before creating the MR or PR, verify both published tips against the reviewed SHAs using fresh remote refs.
3. If either tip changes, recompute the comparison. Repeat review when the source SHA, the diff, or relevant target context changes. Record the validated target SHA even when the existing review still applies.

## Resolve findings and close the review

- Verify each finding against the code or evidence. Briefly explain rejected findings. Report pre-existing problems outside the touched behavior and leave their fixes outside the task unless authorized.
- For a confirmed problem, identify the behavior that must hold and check the affected callers, modes and failure paths within scope for the same cause. Prefer a shared fix where those paths already converge. Add a regression check when needed to catch a failure that existing checks would miss.
- Remove unnecessary code, fix confirmed and actionable findings, and then run the relevant checks.
- After an instruction or plan edit, re-read the whole affected section and check related requirements and exceptions for consistency.
- If anything to be committed or pushed differs from its reviewed version, review the updated material first. Apply the renewed review requirements for changes to the reviewed branch or high-risk operation as well. Running tests or loading a skill alone does not satisfy an independent review requirement.
