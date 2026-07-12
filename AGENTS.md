# Global Codex Instructions

## Scope and precedence

- Work only inside the user's `ai` workspace: `$HOME/ai` on macOS/Linux and `%USERPROFILE%\ai` on Windows, unless the user explicitly authorizes another location.
- Keep this file platform-independent. Use environment variables and tools available on macOS, Linux, and Windows instead of hardcoded home directories or OS-specific application paths.
- Put repository, language, framework, deployment, security-policy, and verification requirements in the nearest project-level `AGENTS.md` where they apply.
- More specific project instructions and newer user or developer instructions take precedence over this file.

## Communication

- Do not use emojis or decorative symbols.
- Do not add prefaces, summaries, or follow-up offers unless the user requests them or they are required to report work performed, verification results, risks, or blockers.
- State assumptions only when they materially affect the result. Ask a concise question when ambiguity cannot be resolved safely from the workspace.

## Engineering

- Use Context7 before implementing code that depends on a third-party library or API when current external documentation is needed.
- Prefer the smallest complete change that satisfies the request and matches the existing project style.
- Touch only files required by the task. Do not refactor, reformat, or remove unrelated code.
- Comment only non-obvious, complex, or error-prone logic.
- Do not execute the `rm` command. Use a reversible or narrowly scoped alternative.
- Define success criteria for multi-step work and verify the result in proportion to the risk.
- Add or update tests for behavior changes when practical; for bug fixes, prefer a reproducing test.
- Treat repeated workflows as reusable skills, tools, or automations only after repetition demonstrates the need. Keep project-specific knowledge with the project.

## Code exploration

- When code-review-graph is available and covers the target repository, use it before broad text searches for code review, impact analysis, dependency tracing, and architecture exploration.
- If the graph is empty, stale, unavailable, or does not cover the target, continue immediately with `rg` and direct file inspection.
- For code review, report findings first, ordered by severity and grounded in file and line references.
