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
- Independent review gate. Get an independent review from Antigravity CLI (`agy`, model `gemini-4-hydrogen-xhigh`, Google AI Pro subscription, not API tokens) in these cases. Never call `codex` for this: you are Codex, so it would review its own work.
  1. Local changes: after finishing code changes in a git repository and before any commit or push, review the complete task diff, including staged, unstaged, and task-owned untracked files.
  2. Plans: before presenting an implementation plan for approval (plan mode, or a plan the user asked for). Not a short progress checklist.
  3. MR/PR: before creating an MR/PR, review the whole branch against its target branch, not only the latest changes.
  4. Someone else's MR/branch the user asks to review: run agy as a second opinion next to your own review. Check the branch out in a separate `git worktree` so the user's working tree stays untouched.
  5. Incident diagnosis: before presenting a root-cause conclusion, or proposing or making a fix based on it, have agy check the conclusion against the evidence.
  6. Instruction edits: changes to `AGENTS.md`, `CLAUDE.md`, rules, skills, config or hooks, including files outside git.
- Skip this gate when you are the reviewer: in the `codex review` command, or in `codex exec` started with a review request (another agent's gate), review the material yourself and call no other reviewer (agy, Codex, or a review skill run as a separate process). Case 4 above applies only when the user asks for the review in a chat; the `codex review` command is always treated as a nested gate. Reason: Claude Code's review gate runs `codex review`; a nested agy run there added minutes and Google quota and wrote files outside the repository (2026-11-19).
- How to run it. agy has no review subcommand, so the prompt names the scope: for local changes, `git diff HEAD` plus the task-owned untracked files by path; for a branch, `git diff <target-branch>...HEAD`; for a commit, `git show <SHA>`; otherwise a request file with the material (plan text; diagnosis with evidence locations; before/after text of instruction edits) by absolute path. Run from the repository root, or from a temporary directory outside git, and wait for it to finish before passing the gate (commit, push, MR, plan approval, fix): `agy -p "<scope>. Report concrete problems only, each with file:line and a fix. Do not modify files." --model gemini-4-hydrogen-xhigh --mode plan --print-timeout 900s </dev/null`. A run takes several minutes.
- Plan mode is not a write barrier (agy auto-approves commands here), so record `git status --porcelain -uall`, `git diff HEAD | shasum` and `shasum` of task-owned untracked files before and after (outside git, `shasum` of the reviewed files); if anything changed, stop and tell the user.
- Treat each agy finding as a claim: verify it against the code or evidence, act on confirmed ones, and briefly report rejected ones with the reason.
- If agy is unavailable (command missing, not logged in, usage limit reached, model unavailable, unsupported location, or an error without a result), say so in one line and review it yourself: `ponytail:ponytail-review` for code diffs, a critical self-review for plans, diagnoses and instruction edits.
- Reason: the user wants an independent review of local changes, plans, MRs, incident diagnoses and instruction edits; Claude Code uses Codex for it, and Codex uses agy (2026-11-18).
- Remove unnecessary code and fix actionable findings, then run the relevant checks. If the diff changes, review it again before committing or pushing. Loading the skill or passing tests alone does not satisfy this gate.
- A completed review covers both commit and push while the reviewed task diff is unchanged. Reuse its result; repeat review only after a relevant diff change or new finding.

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
- Apply Ponytail session modes only when explicitly requested. Use `ponytail:ponytail-review` as the fallback review of code diffs when agy is unavailable.

## Skill Creation and Updates

- Use `skill-creator` before creating or substantially updating a skill.
