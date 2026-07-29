# Global Codex Instructions

## Scope and precedence

- Work across the local filesystem when needed for the user's task. Treat destructive operations and external side effects with appropriate care.
- Keep this file platform-independent. Use environment variables and tools available on macOS, Linux, and Windows instead of hardcoded home directories or OS-specific application paths.
- Put repository, language, framework, deployment, security-policy, and verification requirements in the nearest project-level `AGENTS.md` where they apply.
- More specific project instructions and newer user or developer instructions take precedence over this file.

## AI workspace layout

- When working under the user home directory's `ai/` workspace, store project context and documentation in `ai/projects/`.
- Store project source code in `ai/code/`.
- Store, upload, and process temporary data only in `ai/temp/`.
- For every project, maintain project-local `memories/` and `rules/` directories in its context root. Put durable project knowledge and decisions in `memories/`, and operational or engineering requirements in `rules/`. Read the relevant files before work and keep them current; update memory only when the user explicitly asks to persist it.

## Communication

- Do not use emojis or decorative symbols.
- Do not add prefaces, summaries, or follow-up offers unless the user requests them or they are required to report work performed, verification results, risks, or blockers.
- State assumptions only when they materially affect the result. Ask a concise question when ambiguity cannot be resolved safely from the workspace.

## Engineering

- Prefer the smallest complete change that satisfies the request and matches the existing project style.
- Touch only files required by the task. Do not refactor, reformat, or remove unrelated code.
- Comment only non-obvious, complex, or error-prone logic.
- Do not execute `rm -rf` unless the user explicitly approves the exact command and target path. Prefer reversible or narrowly scoped alternatives.
- Define success criteria for multi-step work and verify the result in proportion to the risk.
- Add or update tests for behavior changes when practical; for bug fixes, prefer a reproducing test.
- Treat repeated workflows as reusable skills, tools, or automations only after repetition demonstrates the need. Keep project-specific knowledge with the project.

## Code exploration

- When code-review-graph is available and covers the target repository, use it before broad text searches for code review, impact analysis, dependency tracing, and architecture exploration.
- If the graph is empty, stale, unavailable, or does not cover the target, continue immediately with `rg` and direct file inspection.
- For code review, report findings first, ordered by severity and grounded in file and line references.
