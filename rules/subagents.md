# Working with subagents

## When to delegate

These rules authorize bounded delegation within the current chat when the tools are available and the active session and project instructions allow it. The main agent owns the outcome, user communication, approvals, and final verification.

- Delegate a substantial read-only lookup across many files, large logs, or query results when the useful output is a short list of facts with references. Give it a specific question and use an explorer for codebase questions. Keep routine lookups in the main agent and use the facts to make the diagnosis there.
- Once scope is settled, use workers for independent changes or checks that can progress in parallel. Work is independent when it can proceed without another agent's unfinished result and its edits have an exclusive owner. Start dependent work once its prerequisite is available. Keep short, sequential, or context-heavy work in the main agent.
- Seek a focused second opinion for a costly conclusion where it adds useful scrutiny. For a bounded code review, use a read-only subagent and choose the reviewer role if the session provides one. Follow the [review rules](review.md), including their restrictions on nested review. A subagent's opinion does not satisfy the independent review gate.
- Honor the user's explicit delegation, model, and effort instructions. Use the session defaults for routine delegation and override them only when the user or applicable instructions specify the override. Report an unavailable requested role, model, or effort before substituting it.

## Assign the work

- Give each subagent the goal, relevant repository and paths, settled decisions, constraints, expected result, and how to verify it. Include the applicable instructions and the minimum context needed. Share only data the subagent is authorized to use.
- Mark lookups and reviews as read-only. For edits, specify the files or modules the worker owns. Tell workers that other people or agents may be editing the repository, to preserve unrelated changes, and to report any conflict or need to expand their scope before editing outside it.
- Give each file a single writer at a time, including the main agent. Use separate worktrees when parallel branches are needed or a shared working tree would mix changes. Check for work already in progress before assigning or taking over a task.
- State in each brief that subagents may not commit, push, open or merge MRs/PRs, deploy, act on production, or send external communications. The main agent owns those actions within the user's authorization and project gates. Subagents do not delegate further unless the user explicitly authorizes nested delegation.

## Verify and integrate results

- Ask for a concise result with relevant references or diffs, checks run and their outcomes, and any blockers or unverified assumptions. Have edit workers report which files they changed.
- Check results against the diff, primary evidence, or relevant checks before integrating them or starting dependent work. For edits, verify the combined behavior at the normal entry points. Keep work assigned to its owner until it finishes or hands it back. If a worker is blocked, let independent work continue. Before reassigning edits, confirm the previous owner has stopped editing those files.
- Use bounded waits for outstanding work and check the current state before retrying any step. After verification, close completed subagents when the tool supports it and release task-owned temporary resources that are no longer needed. Preserve work and evidence still in use.

## Keep the current chat responsible

Use subagents for work inside the current chat. Create a separate user-owned chat only when the user explicitly asks for one. Keep CI, rollout, and other completion monitoring in the owning chat with bounded checks and follow through until the requested condition is met. Follow project approvals at each stage.
