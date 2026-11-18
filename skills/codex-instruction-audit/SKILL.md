---
name: codex-instruction-audit
description: Audit actual Codex model usage, settings synchronization, and global/project instructions without changing them. Use for a requested or scheduled Codex configuration and instruction audit, including recurring weekly audits. Do not use for routine code review or component updates.
---

# Codex Instruction Audit

Run a read-only audit of Codex models, settings, and global/project instructions on this Mac.

First determine the primary model actually used during the last seven days. Prefer existing usage summaries or lightweight main-agent turn metadata; exclude scheduled runs and subagents where distinguishable. State the counting method, coverage, and confidence. Do not read full conversations or tool logs merely to count models. Compare actual use with the configured default. If usage evidence is unavailable, explicitly label the configured model as a fallback rather than measured usage.

For that exact model, find and open current official OpenAI guidance on prompting, reasoning, tools, context, and agent workflows. Use the OpenAI Docs skill and cite specific official pages with the check date. Do not silently substitute another model or confuse public documentation with this account's availability. Check retirement or unavailable-model risks in relevant current settings, agent routes, and scheduled tasks without surveying the entire model catalog.

Compare installed global AGENTS.md and applicable overrides/configuration with the synchronization source at /Users/dk/.local/share/codex-settings. Inspect relevant synchronization behavior and user-managed skills. Check project AGENTS.md, linked task-relevant rules, and workflows in /Users/dk/ai/alvend and /Users/dk/ai/beeline/biometry-3.0; include other projects only when recent activity makes them relevant. Account for separate service Git roots, actual instruction/skill discovery, and locally changed or unpublished instruction dependencies. Read connected sections selectively, reuse unchanged evidence, batch independent reads, and keep tool output small.

Identify concrete contradictions, duplicate active instructions/skills, stale guidance, broken workflow routing, and requirements that cause unnecessary discovery, clarification, reading, repeated review/tests, handoffs, or output. Distinguish correctness/security issues from optional token optimizations. Preserve agreed acceptance checks, secret protections, PROD approvals, rollback rules, legacy boundaries, and review gates; suggest reuse of unchanged verification rather than removal of necessary checks. Do not claim measured token savings without measurements.

Report concisely in Russian: the primary model and evidence, material changes since the previous audit when available, then prioritized actionable findings. For each finding give the exact file/section, a concrete consequence, the smallest proposed fix with English replacement wording where useful, supporting evidence/official links, and any verification limit. Avoid repeating unresolved recommendations unless their status or evidence changed; if there are no actionable findings, give one short conclusion.

Do not edit instructions, settings, skills, memories, or application files; do not install/update components, change models, commit, push, deploy, or contact anyone. This task only audits and proposes improvements.

## Model usage helper

Prefer an existing usage summary when it covers the requested period and distinguishes primary turns, subagents, and scheduled runs. Otherwise run the bundled read-only helper:

```sh
python3 <skill-directory>/scripts/model_usage.py --days 7 --end <audit-time-with-UTC-offset>
```

Use the heartbeat's `current_time_iso` as the audit end when present. For an interactive audit, use the actual check time. Resolve `<skill-directory>` from this skill's installed location. Python 3.11 or later is required. `--codex-home` is available for another explicitly selected local Codex home.

The helper queries local SQLite metadata in read-only mode and seeks only to bounded turn-start records for `task_started` attribution and `turn_context` model/effort. It skips message bodies and never parses conversations or tool results. It counts completed primary turns, excludes identifiable subagents and scheduled runs, and reports unknown triggers, missing metadata, exclusions, and coverage. It reads only the configured model/effort for comparison; that configuration is never counted as measured usage.

Interpret the coverage before naming a primary model. A tie, unavailable database, missing contexts, or unclassified triggers must remain visible; do not silently replace missing measurements with the configured default. Local history is not complete account-wide usage. Missing metadata is a verification limit, not a reason to scan full conversations or logs.

## Reuse and reporting

Use the previous audit in the current chat as the comparison baseline when available. If it is absent, retrieve only the relevant prior final report or state that no baseline is available; do not reconstruct it by reading all tool logs. Reuse unchanged evidence and inspect changed content rather than treating a modification timestamp alone as a new finding.

Keep the required model evidence and source-check date in the concise report. For a heartbeat, follow its notification rules: routine unchanged results stay quiet; notify only for a new material recommendation, a changed finding, a model-retirement risk, or an important verification blocker. Do not repeat unresolved recommendations just because another run occurred.
