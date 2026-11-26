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
- Read and follow the [review rules](rules/review.md) under `$CODEX_HOME` (default `~/.codex`) after finishing code changes and before committing, pushing, creating an MR/PR, reviewing a branch or MR/PR, presenting an implementation plan for approval, reporting or acting on an incident diagnosis, editing instructions, rules, skills, config or hooks, or executing high-risk work. Follow them when handling findings. If the file cannot be read, report it and pause high-risk execution.

### Merge Requests and Pull Requests

- Never mention Codex, Claude, ChatGPT or AI assistance in commit messages or in MR/PR titles, descriptions or comments. Omit AI co-author trailers and "generated with" lines.
- Describe briefly what changed and how the problem was solved. Omit check logs, deployment status and verification plans unless requested. Project rules for the description format, such as Jira links, still apply.
- When posting MR/PR, Jira or other API text with non-ASCII content (Cyrillic), build the JSON from real UTF-8 strings (e.g. `json.dumps` of a Python literal, or `glab`/`gh` with a body file); never pass text through `unicode_escape`, shell `printf` escapes or other re-encoding. Read the created text back from the API and check it before reporting. Reason: a `unicode_escape` round-trip once garbled the Cyrillic in four MR descriptions.

## 5. Goal-Driven Execution

- For behavior changes, run the smallest useful check. Reproduce a reported bug before fixing it when feasible.
- For refactors, compare behavior before and after.
- For UI layout or style changes, check in a browser the states users actually reach, not only the first screen: a scrolled page under fixed or sticky elements, every theme, and a narrow width. Reason: a restyle once made a sticky header transparent; the first screen looked right, but content showed through it on scroll and the regression reached production. Do not add mobile-specific layout code (media queries, narrow-width tweaks) unless the user asks for mobile support. Reason: the user rejected unrequested mobile adaptations.
- For multi-step tasks, state a concise plan with a check for each step.
- Read and follow the [subagent rules](rules/subagents.md) under `$CODEX_HOME` (default `~/.codex`) when deciding whether to delegate, assigning work, or verifying subagent results.
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
- Apply Ponytail session modes only when explicitly requested.

## Skill Creation and Updates

- Use `skill-creator` before creating or substantially updating a skill.
