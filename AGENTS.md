# AGENTS.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.
- Verify current library and framework documentation through Context7; if it is unavailable, use the official vendor documentation and state the fallback.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Natural, Specific Writing

- Write for immediate comprehension. Use concrete terms and unambiguous statements; remove vague abstractions and wording that permits multiple interpretations.
- Be concise. Remove filler, generic introductions, tangents, and details that do not change the task or result.
- Use active, modern language. Avoid bureaucratic phrasing, passive voice, deeply nested clauses, and long chains of nouns.
- Match the style and depth established by the request or supplied material. When no style is specified, use concise informational writing.
- Stay within the requested scope. Add unrequested background only when it changes the conclusion, decision, or safe execution of the task.
- Avoid formulaic transitions, repeated discourse markers, recurring rhetorical templates, and unusually uniform sentence structure. Do not imitate a person or make claims about authorship.

Keep rules and instructions compact and grouped by topic. Extend the closest existing section instead of scattering related guidance across new sections or files. Write all rules and instructions in English.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
