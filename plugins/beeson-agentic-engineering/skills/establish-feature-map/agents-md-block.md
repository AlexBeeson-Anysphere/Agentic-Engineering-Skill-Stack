# AGENTS.md Block

Insert this block between `<!-- agent-map:start -->` and `<!-- agent-map:end -->` in the root `AGENTS.md` (and `CLAUDE.md` if present). If the markers already exist, replace everything between them; otherwise append to the end of the file after a blank line.

```markdown
<!-- agent-map:start -->
## Agent feature map (`agent-map/`)

This repository maintains a behavior-and-code feature map in [`agent-map/README.md`](agent-map/README.md). Use it as your primary anti-spiral mechanism before exploring the repo with broad searches.

1. **Orient first:** Read [`agent-map/README.md`](agent-map/README.md) for the stack overview, verification harness baseline, **Features (regression sweep order)** index, and **Common tasks → start here** router.
2. **Load only the scoped feature:** Open the single `agent-map/<feature>.md` file matching your task (do not read every feature file into context). Each file tells you:
   - What sub-features exist and how a user/caller reaches them
   - How to drive and verify the behavior (preconditions, commands, observable proof)
   - Exact code touchpoints (entry routes, handlers, state/schema, tests, dependencies)
   - Gotchas ("what usually lies" in code and runtime verification)
3. **Search narrowly:** Once `Code touchpoints` gives you the exact directories and entry files, scope `rg`/file reads to those paths.
4. **Pass context to subagents:** When spawning subagents, pass the relevant `agent-map/<feature>.md` path in their prompt so they start oriented without re-exploring the repo.
5. **Keep the map honest:** If your change alters user-visible behavior, entry routes, verification commands, or key touchpoints, update the matching `agent-map/<feature>.md` in the same change (or run `maintain-feature-map`). Never edit a feature file's `## Notes` section—it is human-maintained.
<!-- agent-map:end -->
```

If no `AGENTS.md` exists at the repository root, create one containing:

```markdown
# Agent Instructions

<!-- agent-map:start -->
...block above...
<!-- agent-map:end -->
```
