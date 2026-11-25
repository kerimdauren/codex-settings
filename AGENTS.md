# AGENTS.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

## 1. Think Before Coding

**Don't hide confusion. Surface tradeoffs.**

Before implementing:
- Identify the requested outcome, scope, authoritative requirements, applicable instructions, and completion checks before dependent work. Reuse settled context and do only the focused discovery needed for this task.
- Resolve currently known material ambiguities together before implementation; present concrete options, tradeoffs, and recommended defaults. Do not reopen settled decisions or ask for information already available. Ask later only when new evidence materially changes the result or risk.
- For routine implementation choices, use the existing pattern and proceed. State an assumption when it affects the result.
- If a simpler approach exists, say so. Push back when warranted.
- Check current official documentation when a decision depends on the version or behavior of an external library, framework, or API. Use Context7 or web search if the official documentation is unavailable.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions or helpers for single-use code.
- No speculative "flexibility" or "configurability" that wasn't requested.
- No defensive error handling for impossible scenarios.

### Default Decision Rule

- Start with the smallest readable solution that satisfies the current task.
- Add complexity only when required by an explicit requirement, observed behavior, or an existing project constraint. Identify that reason.
- A hypothetical edge case alone does not justify additional code. Address it when evidence supports it or its consequences are substantial.
- Do not add layers, interfaces, configuration, retries, fallbacks, or custom error types without a concrete need in the current task.
- Prefer direct code. Extract a helper when it removes meaningful duplication or makes the code easier to understand.
- Before finishing, remove complexity introduced by your changes that is not necessary for the requested behavior.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Avoid unrelated changes to code, comments, or formatting.
- Don't refactor unrelated working code.
- Match existing style, naming conventions, and patterns.
- If you spot unrelated dead code or bugs, mention them in your response — do not edit them.

When your changes create orphans:
- Remove imports, variables, and helpers that YOUR changes made obsolete.
- Keep pre-existing unused code intact unless explicitly instructed.

## 4. Workspace & Git Hygiene

- Don't discard existing work or data unless the user has authorized that loss.
- Name new branches with the `feature/` prefix.
- Never commit secrets, `.env` files, or credential dumps.
- Independent review gate. Use Claude Code CLI (`claude`, model `claude-fable-5-2`, effort `medium`) for independent review in these cases. Use the Claude subscription login. Before running the review, confirm subscription authentication with `claude auth status` from the review directory and check that no API credentials or alternate provider settings override it. Never call `codex` for this: it would review its own work.
  1. Local changes: after finishing code changes in a git repository and before any commit or push, review the complete task diff, including staged, unstaged, and task-owned untracked files.
  2. Plans: before presenting an implementation plan for approval (plan mode, or a plan the user asked for). Not a short progress checklist.
  3. MR/PR: review the whole branch before creating an MR/PR. First fetch the target branch and record its tip SHA and the source tip SHA to be published. Use `git diff <target-sha>...<source-sha>`. Recheck the target and intended source tips after review. Immediately before creating the MR/PR, verify both published branch tips against the reviewed SHAs using fresh remote refs. If either tip changes, recompute the comparison. Repeat review if the source SHA, diff, or relevant target context changed. Record the validated target SHA even if the previous review still applies.
  4. Someone else's MR/branch the user asks to review: run Claude as a second opinion alongside your own review. Check the branch out in a separate `git worktree` so the user's working tree stays untouched.
  5. Incident diagnosis: before presenting a root-cause conclusion, or proposing or making a fix based on it, have Claude check the conclusion against the evidence.
  6. Instruction edits: changes to `AGENTS.md`, `CLAUDE.md`, rules, skills, config or hooks, including files outside git.
  7. High-risk work: complete independent review before executing production database changes, changes to access permissions, bulk operations, or other work with significant impact or limited rollback options. Review the exact commands or change set, target environment and scope, expected impact, verification steps, and rollback or recovery plan. Reuse earlier independent review only if it covered all these details for the operation to be executed. Review again before execution if the commands or change set change, or if any other reviewed detail changes materially.
- Skip this gate in `codex review` or when `codex exec` is started with a review request. Review the material yourself without launching another reviewer. Case 4 applies only to review requests made by the user in chat. Claude Code can call Codex as its reviewer, so a nested call would create a review loop. High-risk execution still requires the independent review in case 7.
- Prepare a review input with the scope, line-numbered evidence where needed, and enough surrounding context to assess behavior. For local changes, include the staged diff (`git diff --cached`), the unstaged diff (`git diff`), and the contents and paths of task-owned untracked files. Scope each diff to the task paths or hunks. Include relevant caller or test excerpts when the diff alone is insufficient. For a branch, use the pinned SHA comparison in case 3; for a commit, use `git show <SHA>`. For high-risk work, include the items listed in case 7. For other reviews, include the plan, diagnosis with supporting evidence, or before/after instruction text. Exclude secrets and unrelated changes. Provide any missing context Claude identifies before accepting the review.
- From a temporary directory outside Git, pass the prepared material on stdin and wait for the result before passing the gate: `claude -p --safe-mode --strict-mcp-config --tools '' --no-session-persistence --model claude-fable-5-2 --effort medium 'Review the supplied material. Report concrete problems only, each with file:line where applicable and a fix. Flag missing context that prevents review.' < "$review_input"`. Use an absolute input path. The reviewer works from the supplied material with tools disabled. Allow up to 15 minutes and treat a timeout as an unavailable result.
- For Git work, record `git status --porcelain -uall` for context before and after review. For local changes, hash the scoped staged and unstaged diffs separately and record the paths and hashes of task-owned untracked files before and after review. Outside Git, hash the reviewed files before and after review. If a hunk-scoped hash changes, compare the reviewed hunks by content to account for unrelated edits in the same file. If the reviewed material changes during review, stop and tell the user. Continue the review through unrelated workspace changes. Keep the reviewed patches and file contents available for commit or push verification. Before committing, verify `git diff --cached` against the reviewed staged changes and any reviewed unstaged changes or task-owned untracked files now staged. Before pushing, verify that all outgoing commits are covered by completed reviews. Compare against the fetched destination tip or, for an unpublished branch, its intended base. Keep unrelated changes out of the commit and push.
- Verify each Claude finding against the code or evidence, act on confirmed findings, and briefly explain any rejected findings.
- If Claude CLI is unavailable (command missing, login unavailable, usage limit reached, model unavailable, or an error without a result), tell the user. For high-risk work (case 7), pause execution until independent review is complete. In other cases, review it yourself: `ponytail:ponytail-review` for code diffs, a critical self-review for plans, diagnoses and instruction edits.
- Remove unnecessary code and fix actionable findings, then run the relevant checks. If any change to be committed or pushed differs from its reviewed version, review it again first. Loading the skill or passing tests alone does not satisfy this gate.
- A completed review covers both commit and push while the outgoing content matches the reviewed changes. Staging already reviewed content after review does not by itself require another review. Reuse the result unless the relevant content changes or there is a new finding.

### Merge Requests and Pull Requests

- Never mention Codex, Claude, ChatGPT or AI assistance in commit messages or in MR/PR titles, descriptions or comments. Omit AI co-author trailers and "generated with" lines.
- Describe briefly what changed and how the problem was solved. Omit check logs, deployment status and verification plans unless requested. Project rules for the description format, such as Jira links, still apply.
- When posting MR/PR, Jira or other API text with non-ASCII content (Cyrillic), build the JSON from real UTF-8 strings (e.g. `json.dumps` of a Python literal, or `glab`/`gh` with a body file); never pass text through `unicode_escape`, shell `printf` escapes or other re-encoding. Read the created text back from the API and check it before reporting. Reason: a `unicode_escape` round-trip once garbled the Cyrillic in four MR descriptions.

## 5. Goal-Driven Execution

- For behavior changes, run the smallest useful check. Reproduce a reported bug before fixing it when feasible.
- For refactors, compare behavior before and after.
- For UI layout or style changes, check in a browser the states users actually reach, not only the first screen: a scrolled page under fixed or sticky elements, every theme, and a narrow width. Reason: a restyle once made a sticky header transparent; the first screen looked right, but content showed through it on scroll and the regression reached production. Do not add mobile-specific layout code (media queries, narrow-width tweaks) unless the user asks for mobile support. Reason: the user rejected unrequested mobile adaptations.
- For multi-step tasks, state a concise plan with a check for each step.
- Read selectively: locate relevant files or symbols first, then inspect needed sections and connected behavior. Reuse unchanged content already available in context; reread only after changes, missing or truncated evidence, or a specific unresolved question.
- Batch independent reads and searches. Start with small tool output budgets, usually 2,000–4,000 tokens, and expand when needed for correctness. Narrow queries and inspect large logs in sections instead of dumping them. Never treat truncated output as complete evidence or omit relevant failures.
- Once scoped checks pass and completion criteria are met, finish. Repeat exploration or checks only for a relevant change, failure, or unresolved concern. Use bounded waits and backoff for external jobs instead of frequent unchanged snapshots.

## 6. Communication & Style

- Propose separate chats when the user asks or splitting independent work materially helps execution or context. Prepare starter prompts only when requested or the split is accepted; include the goal, relevant files, settled decisions, constraints, and acceptance criteria. Do not create chats automatically.

- Respond in the user's language while keeping rules, commit messages, and internal instructions in English.
- Keep progress updates and final answers concise: report conclusions, verification, and material blockers rather than raw logs or repeated plans.
- Extend existing rules and files rather than scattering guidance across new files.


## Corrections, Recurring Habits and Skill Suggestions

- When the user corrects your behavior or points out a mistake that could recur, record the lesson in the same turn without being asked (in read-only work, such as an audit, propose the edit instead): cross-project lessons in the global instructions (edit `AGENTS.md` in the synchronization source `$CODEX_SETTINGS_CHECKOUT`, default `~/.local/share/codex-settings`, and the installed copy in `$CODEX_HOME`, default `~/.codex`; while the checkout has uncommitted changes, sync stops pulling updates from GitHub, so commit and push it when the user allows, otherwise tell the user that updates wait until it is committed), project lessons in the project's `AGENTS.md` or rules (when a checkout's `AGENTS.md` is a Git-ignored pointer to shared project instructions, edit the file it points to). Write it as a general rule with the reason, update an existing rule instead of duplicating it, and tell the user in one line where it was saved. Skip one-off task feedback that will not recur.
- Remember confirmed, recurring user habits at the narrowest applicable scope: project-specific habits in the project's existing instructions or context files, and cross-project habits in global Codex instructions. Keep the global synchronization source consistent with changes; extend existing files and do not turn one-off actions into permanent rules.
- When a workflow repeats frequently or daily, proactively suggest a skill at the appropriate project or global level. Explain the repeated work it would simplify and check existing skills for overlap. Suggest extending an existing skill when suitable; create or substantially update a skill when the user requests it.

## Coding Standards
- Before implementing, refactoring, or reviewing Python/FastAPI or Go services and applications, load and follow the `coding-standards` skill from the available skill catalog. For scripts and small utilities, apply only relevant simplicity rules.
- Use Graphify automatically only for relevant queries against an existing graph. Build or update graphs only when explicitly requested; use direct code search for ordinary lookups and edits.
- Apply Ponytail session modes only when explicitly requested. Use `ponytail:ponytail-review` as the fallback review of code diffs when Claude CLI is unavailable.

## Skill Creation and Updates

- Use `skill-creator` before creating or substantially updating a skill.
