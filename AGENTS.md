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
- Never commit secrets, `.env` files, or credential dumps.
- Before any commit or push, run `ponytail:ponytail-review` on the complete task diff, including staged, unstaged, and task-owned untracked files. For already committed changes, review the outgoing commit diff.
- Remove unnecessary code and fix actionable findings, then run the relevant checks. If the diff changes, review it again before committing or pushing. Loading the skill or passing tests alone does not satisfy this gate.

## 5. Goal-Driven Execution

- For behavior changes, run the smallest useful check. Reproduce a reported bug before fixing it when feasible.
- For refactors, compare behavior before and after.
- For multi-step tasks, state a concise plan with a check for each step.
- Read selectively: locate relevant files or symbols first, then inspect needed sections and connected behavior. Reuse unchanged content already available in context; reread only after changes, missing or truncated evidence, or a specific unresolved question.
- Batch independent reads and searches. Start with small tool output budgets, usually 2,000–4,000 tokens, and expand when needed for correctness. Narrow queries and inspect large logs in sections instead of dumping them. Never treat truncated output as complete evidence or omit relevant failures.
- Once scoped checks pass and completion criteria are met, finish. Repeat exploration or checks only for a relevant change, failure, or unresolved concern. Use bounded waits and backoff for external jobs instead of frequent unchanged snapshots.

## 6. Communication & Style

- After analyzing a large task, if independent subtasks emerge, propose splitting them. For each subtask, prepare a short starter prompt for a new chat covering the goal, relevant files, agreed decisions, constraints, and acceptance criteria. Include only the context needed to avoid repeating the analysis. If the subtasks are tightly coupled and continuing in the current chat is more efficient, briefly explain why. Do not create new chats automatically.

- Respond in the user's language while keeping rules, commit messages, and internal instructions in English.
- Keep progress updates and final answers concise: report conclusions, verification, and material blockers rather than raw logs or repeated plans.
- Extend existing rules and files rather than scattering guidance across new files.


## Coding Standards
- Before implementing, refactoring, or reviewing Python/FastAPI or Go services and applications, load and follow the `coding-standards` skill from the available skill catalog. For scripts and small utilities, apply only relevant simplicity rules.
- Use Graphify automatically only for relevant queries against an existing graph. Build or update graphs only when explicitly requested; use direct code search for ordinary lookups and edits.
- Apply Ponytail session modes only when explicitly requested. This does not change the required `ponytail:ponytail-review` before commit or push.
