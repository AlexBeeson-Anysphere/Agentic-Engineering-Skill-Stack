---
name: establish-feature-map
description: Builds a repository's centralized Agent Feature Map in `agent-map/` (`README.md` index + one `.md` file per feature) combining user-POV behavior, verification recipes, code touchpoints, and gotchas, and wires `AGENTS.md` to use it as an anti-spiral index. Works on any stack (web, mobile, API, CLI, workers, monorepo). Use when creating an `agent-map/` from scratch, migrating from scattered docs, or doing a full architectural remap.
disable-model-invocation: true
---

# Establish Agent Feature Map (`agent-map/`)

Build the repository's centralized, checked-in `agent-map/` directory so any local agent, Cloud Agent, or CI automation can orient in two hops (`AGENTS.md` → `agent-map/README.md` → `agent-map/<feature>.md`) without burning tokens on broad codebase exploration.

Each feature file unites **user-POV behavior & verification recipes** (Lauren Tan's Feature Map model) with **exact code touchpoints & dependencies**, stamped with a git SHA and tracked `Paths:` so `maintain-feature-map` can lint it against drift.

`$SKILL_DIR` is the directory containing this `SKILL.md`. Use its absolute path when running scripts or prompting subagents.

## What a Finished Run Produces

1. **`agent-map/README.md`** — Stack & architecture overview, baseline & verification harness commands, top-to-bottom **Features (regression sweep order)** table, **Common tasks → start here** router, and global gotchas.
2. **`agent-map/<feature-slug>.md` (one file per feature)** — Typically 4–20 files depending on repo size, each ≤ 150 lines, following [FEATURE-TEMPLATE.md](FEATURE-TEMPLATE.md) and stamped with `<!-- agent-map v2 | Last linted: <sha> | Paths: <repo paths> -->`.
3. **Root `AGENTS.md` (and `CLAUDE.md` if present)** — Wired with the `<!-- agent-map:start -->` block from [agents-md-block.md](agents-md-block.md).
4. **Zero validation errors** when running `python3 $SKILL_DIR/scripts/validate.py <root>`.

## Hard Rules

1. **Follow [FEATURE-TEMPLATE.md](FEATURE-TEMPLATE.md) verbatim.** Exact H2 headings and order. `validate.py` enforces them.
2. **Slice by feature, not by folder or file.** Do not create scattered `MAP.md` files in source subdirectories. Everything lives in `<repo-root>/agent-map/`. See [feature-discovery-guide.md](feature-discovery-guide.md).
3. **Evidence over guesswork.** Every route, CLI flag, test/harness command, file path, dependency, and gotcha must come from reading actual code, manifests, or tests.
4. **Preserve `## Notes`.** If an existing `agent-map/*.md` file has content under `## Notes`, carry it over verbatim.
5. **Clean up legacy scattered `MAP.md` files only if migrating.** If `discover.py` reports legacy scattered `MAP.md` files outside `agent-map/`, fold their useful insights and `## Notes` into the appropriate `agent-map/<feature>.md` files and ask before deleting more than 3 files.
6. **Never edit product code.** Only `agent-map/*.md` and `AGENTS.md` / `CLAUDE.md` are written.

## Workflow

Copy this checklist into a todo list and track progress:

```text
- [ ] 1. Run scripts/discover.py to inventory stack, harnesses, and candidate surfaces
- [ ] 2. Interview the codebase & design the feature slice plan (regression sweep order)
- [ ] 3. Dispatch parallel subagents to trace features and write agent-map/<feature>.md
- [ ] 4. Write agent-map/README.md from subagent digests
- [ ] 5. Wire AGENTS.md (and CLAUDE.md if present)
- [ ] 6. Validate with scripts/validate.py and fix any errors
- [ ] 7. Report summary and any product ambiguities
```

### 1. Run Discovery

```bash
python3 $SKILL_DIR/scripts/discover.py <root> --summary
```

Inspect the output for:
- Detected languages, manifests, and monorepo markers
- Existing verification skills (`.cursor/skills/verify-*/SKILL.md`) or test harnesses
- Existing `agent-map/*.md` files (and whether they have custom `## Notes`)
- Candidate feature/surface directories

### 2. Design the Feature Slice Plan

Read the root manifest(s), primary router/entry files, and any existing `.cursor/skills/verify-*/features/` files. Using [feature-discovery-guide.md](feature-discovery-guide.md), build a proposed feature table ordered in **top-to-bottom regression sweep order** (bootstrap/auth → core creation → core consumption/search → secondary/async workflows → billing/admin):

| # | Feature File | User / Caller Surface | Tracked `Paths:` |
|---|--------------|-----------------------|------------------|
| 1 | `agent-map/auth-and-sessions.md` | `/login`, `POST /api/auth/*` | `apps/web/src/features/auth`, `apps/api/src/auth` |
| 2 | `agent-map/notes-crud.md` | `/notes`, `notes create` | `apps/web/src/features/notes`, `apps/api/src/notes` |

Check that:
- Every user-facing or caller-facing capability has a home.
- `Paths:` are specific enough that unrelated commits won't mark every feature stale, while collectively covering the active product code.
- Total feature count stays compact (4–8 for small repos, 8–15 for medium, 12–25 for large monorepos).

Display the plan table in chat and proceed immediately.

### 3. Dispatch Parallel Subagents

Create `<root>/agent-map/` if it doesn't exist.

- For repos with **4+ features**, group the features into batches of 1–3 related features and launch parallel subagents via `Task` (`subagent_type: generalPurpose`) using [subagent-prompt.md](subagent-prompt.md).
- For tiny repos (**1–3 features**), trace and write the feature files directly without subagents.

Give each subagent:
- Repo root and current short git SHA (`git rev-parse --short HEAD`, or `nogit`)
- Absolute paths to `$SKILL_DIR/FEATURE-TEMPLATE.md` and `$SKILL_DIR/feature-discovery-guide.md`
- Any existing verification skill path or test runner command
- Its assigned feature slugs, candidate `Paths:`, and any existing `## Notes` to preserve

Each subagent writes its assigned `agent-map/<feature>.md` file(s), validates them with `validate.py --only ...`, and returns a structured digest.

### 4. Write `agent-map/README.md`

Using the subagent digests and [FEATURE-TEMPLATE.md](FEATURE-TEMPLATE.md), write `agent-map/README.md`:
- **Stack & architecture at a glance:** apps/services, shared packages, data stores, how pieces talk.
- **Baseline & verification harness:** exact install, start, health/ready check, verification skill or E2E runner, and fast static check commands.
- **Features (regression sweep order):** numbered table linking to every `./<feature>.md` with its user/caller surface and key code paths.
- **Common tasks → start here:** practical routing table for typical agent requests.
- **Global gotchas:** repo-wide traps (codegen, env vars, build ordering, shared ports/DB).
- **Notes:** preserve existing `## Notes` if updating.

### 5. Wire `AGENTS.md` / `CLAUDE.md`

Follow [agents-md-block.md](agents-md-block.md):
- If root `AGENTS.md` (and/or `CLAUDE.md`) exists: replace the `<!-- agent-map:start --> ... <!-- agent-map:end -->` block if present, or append it to the end of the file.
- If neither exists at the repo root: create `AGENTS.md` with `# Agent Instructions` and the block.

### 6. Validate

```bash
python3 $SKILL_DIR/scripts/validate.py <root>
```

Fix every reported error (missing sections, section order, broken relative links, non-existent `Paths:`, unindexed sibling files, missing `Preconditions:`) and re-run until errors = 0.

### 7. Report

Summarize:
- Feature files created/updated in `agent-map/` (with the regression sweep table)
- Verification harness wired in `agent-map/README.md`
- `AGENTS.md` / `CLAUDE.md` status
- `validate.py` result
- Any dead-looking surfaces, ambiguous boundaries, or suspected bugs noticed while reading the source

## Resources

- [FEATURE-TEMPLATE.md](FEATURE-TEMPLATE.md) — Exact contract for `agent-map/README.md` and `agent-map/<feature>.md`
- [feature-discovery-guide.md](feature-discovery-guide.md) — How to slice features across any stack and order the regression sweep
- [agents-md-block.md](agents-md-block.md) — Block wired into `AGENTS.md` / `CLAUDE.md`
- [subagent-prompt.md](subagent-prompt.md) — Prompt template for parallel feature-tracing subagents
- `scripts/discover.py` — Repo stack & surface discovery (stdlib Python 3)
- `scripts/validate.py` — Contract, link, path, and staleness linter (stdlib Python 3)
