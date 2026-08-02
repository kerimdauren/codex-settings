---
name: biometry-3-operator
description: "Work on Biometry 3.0 (B3) and its b3-* services: investigate, change, test, review, or release code and cross-service contracts."
---

# Biometry 3.0 operator

Treat B3 as a multi-repository system. Evidence must match the requested repository and revision.

## Start safely

1. Source is `~/ai/code/beeline/biometry-3.0/<service>`. Treat project context (usually `~/ai/workspace/beeline/projects/biometry-3.0`) as documentation unless it contains the requested artifact.
2. Read applicable `AGENTS.md` files. Before changing code, inspect the target repo, branch, remotes, worktree, and relevant flow.
3. Keep scope to the requested service/files. Trace callers and the end-to-end contract; fix the shared root cause, not one caller.
4. For cross-service work, identify the owner of each wire, Redis, database, or event contract. Preserve keys, payloads, TTLs, status codes, auth, and side effects unless explicitly changing them.

## Choose the operation

- **Analysis, diagnosis, review, plan:** read-only; separate confirmed evidence, inference, and missing proof.
- **Code change:** smallest complete fix, focused regression check for non-trivial behaviour, then validate.
- **Branch/environment comparison:** fetch/prune first; compare refs, trees, config, and relevant code.
- **MR review:** fetch `refs/merge-requests/<iid>/head` into an isolated worktree, inspect the complete diff, and finish with `Approve` or `Request changes`. Do not post or alter the author branch unless asked.
- **Commit:** review the full staged set and provide a concise Russian message after validation.
- **Push/release:** only when requested; fetch/rebase on the remote tip and repeat relevant checks.

## Implement conservatively

- Reuse local patterns and installed dependencies before adding code or packages. Do not refactor unrelated code.
- In Python services, keep `api -> application -> domain`; infrastructure implements application dependencies. Keep DTOs, domain models, and storage records distinct. Do not add generic `utils.py`, `helpers.py`, or needless interfaces.
- Put settings-backed operational thresholds and timeouts in service settings and inject them at composition. Keep authentication and input validation at trust boundaries.
- Use current primary documentation before changing a third-party API or library contract.
- Do not build Docker images locally. Inspect Dockerfile/Compose changes statically and leave image builds to CI.
- Never expose secrets, tokens, client credentials, or personal data in output, code, tests, logs, commits, or task artifacts.

## Validate and report

1. Run the narrowest meaningful checks: formatter/linter, focused tests, and `git diff --check`; extend to the service suite when practical. Use the documented runtime (often `uv run python -m pytest`).
2. For runtime, migration, or deployment diagnoses, confirm deployed branch, image, entrypoint, and configuration before naming a cause. State missing assets, blocked integrations, and skipped checks as blockers.
3. For performance, use the same workload and baseline; report actual, absolute, and percentage deltas. Label a different measurement as a new step, not a comparison.
4. Report outcome first, then changed files, validation, and blockers/risks. Static code cannot prove production or long-run behaviour.

## Service-specific guardrails

- For Redis-backed antifraud or dashboard work, trace the current `b3-sdk-api` key, hash, JSON, TTL, and cleanup contract before writing code. Do not create a parallel projection accidentally.
- For liveness memory or model work, distinguish a code mitigation from load-test/RSS evidence; fetch before reporting branch differences.
- For OCR/model work, verify model assets and recognition parity. A synthetic speed result is not an end-to-end performance result.
- For outbox, sessions, and migrations, verify transactional boundaries, retry/duplicate semantics, retention, and PII allowlists.
- For dashboards and frontends, validate API request/response and asynchronous stale-response behaviour, not only a successful build.
