# AGENTS.md Block

Insert this block between `<!-- agent-map:start -->` and `<!-- agent-map:end -->` in the root `AGENTS.md` (and `CLAUDE.md` if present). If the markers already exist, replace everything between them; otherwise append to the end of the file after a blank line.

```markdown
<!-- agent-map:start -->
## Agent feature map (`agent-map/`) & verification rig

This repository maintains a behavior-and-code feature map in [`agent-map/README.md`](agent-map/README.md). Use it as your primary anti-spiral mechanism before exploring the repo with broad searches.

1. **Orient first:** Read [`agent-map/README.md`](agent-map/README.md) for the stack overview, verification harness baseline, **Features (regression sweep order)** index, and **Common tasks → start here** router.
2. **Load only the scoped feature:** Open the single `agent-map/<feature>.md` file matching your task (do not read every feature file into context). Each file tells you:
   - What sub-features exist and how a user/caller reaches them
   - How to drive and verify the behavior (preconditions, commands, observable proof)
   - Exact code touchpoints (entry routes, handlers, state/schema, tests, dependencies)
   - Gotchas ("what usually lies" in code and runtime verification)
3. **Search narrowly:** Once `Code touchpoints` gives you the exact directories and entry files, scope `rg`/file reads to those paths.
4. **Prove it with the verification rig:** When `.cursor/skills/run-verification-rig/SKILL.md` exists, use it (`diff`, `feature <slug>`, or `sweep` mode) to drive the real surface and capture proof artifacts under `.verification-evidence/` before declaring work complete. Never treat a passing build alone as proof.
5. **Pass context to subagents:** When spawning subagents, pass the relevant `agent-map/<feature>.md` path (and `.cursor/skills/run-verification-rig/SKILL.md` for verifiers) in their prompt so they start oriented without re-exploring the repo.
6. **Keep the map honest:** If your change alters user-visible behavior, entry routes, verification commands, or key touchpoints, update the matching `agent-map/<feature>.md` in the same change (or run `maintain-feature-map` / `maintain-verification-rig`). Never edit a feature file's `## Notes` section—it is human-maintained.
<!-- agent-map:end -->
```

If no `AGENTS.md` exists at the repository root, create one containing:

```markdown
# Agent Instructions

<!-- agent-map:start -->
...block above...
<!-- agent-map:end -->
```
