# Attribution

This skill is adapted from **pstack** by Lauren Tan (poteto), specifically the `poteto-mode` router skill and its playbooks.

- Source: https://github.com/cursor/plugins/tree/main/pstack
- Router source: `pstack/skills/poteto-mode/SKILL.md`
- Playbook source: `pstack/skills/poteto-mode/playbooks/`
- Principle sources: `pstack/skills/principle-*/SKILL.md`
- Reviewed at: pstack plugin version 0.15.36, `cursor/plugins` commit `ae5650febf4320793844c12c4adaa937f417f8da` (2026-10-31)
- Licence: MIT. Copyright (c) 2026 Lauren Tan. The MIT licence permits use, copying, modification, and distribution, with the copyright and permission notice included. Full text: https://github.com/cursor/plugins/blob/main/pstack/LICENSE

## What was reused

- The routing model: match the request to one playbook, copy its steps verbatim into the task list, keep a skipped step visible with `skip: <reason>`, and require evidence before reporting success.
- All 23 playbook structures, in the same filenames, with their ownership lines, step order, and Reply contracts largely preserved.
- The `figure-it-out` fallback, converted from a pstack skill into `playbooks/figure-it-out.md` so the router has a playbook-shaped escape hatch.
- The supporting ideas named in the router: lead plans/reviews/verifies while subagents implement, the verifier is never the author, Arena (same task, several models, synthesise) vs Swarm (split task, coverage, one combined report), atomic verifiable units, and Opening a PR invoked at the end of every code-changing playbook.
- The engineering-principle leaves supplied for this user persona. They now live in the sibling `engineering-principles` skill, which selects the smallest relevant set; the leaves are guideline files and load only when selected.

## What was changed, and why

This adaptation is oriented differently from pstack on purpose, for use outside Lauren's own repos:

1. **No hard-coded model slugs.** pstack pins model slugs per role (for example a fast code model and a judgment model). This router names roles and a selection rule instead, and defers to whatever per-role configuration the project already has. Slugs age; the rule does not.
2. **No assumed operational companion skills.** pstack playbooks call bundled skills by name (`how`, `why`, `architect`, `arena`, `swarm`, `unslop`, `deslop`, and others) and two `cursor-team-kit` control skills. Here those calls became named capabilities in the router's Supporting capabilities table: use the project's skill of that name if one is installed, otherwise do the action inline. The engineering-principle leaves are references selected through the sibling `engineering-principles` catalog. Nothing requires pstack or `cursor-team-kit` to be installed.
3. **No assumed forge tooling.** GitHub/Origin dual-forge handling, a bundled PR-watcher script, a worktree-audit script, and a plan-checker script were replaced with "resolve the forge and tooling the project already uses, once, and record it." Where a script carried a real rule, the rule stayed in prose (for example: audit worktrees from `git worktree list`, never hand-typed paths).
4. **Layers 1-2 wired in as pre-flight.** This router sits on top of the Feature Map and the verification harness in Scaled Agentic Engineering. Step 0 of `SKILL.md` checks for both before routing and scopes Feature Map reads to one feature file. pstack's router assumes its own verification skills exist; this one names the gap when they do not.
5. **Prose rules dropped.** pstack's reply-writing and comment rules (sentence shape, punctuation bans) are Lauren's working style, not routing machinery. They were not carried over, except: short declarative reporting, every claim carrying its evidence or its label, and never fabricating a link.
6. **`multi-phase-plan.md` condensed.** pstack's version is a full plan document with a long embedded skeleton and a checker script. This version keeps the skeleton and the verification rule (unit, live, and perf boxes, all checked, tests alone insufficient) and replaces the script gate with an explicit self-check step.

If you run pstack itself, prefer upstream `poteto-mode`. This skill exists for projects that want the router and playbooks without adopting the rest of the stack.
