---
name: maintain-feature-map
description: Lints and maintains a repository's `agent-map/` feature map against code drift. Detects stale feature files via git SHA and tracked `Paths:`, flags unmapped code churn, dispatches targeted subagents only for dirty or new features, separates map drift from product regressions, runs optional verification/test checks, and validates contract hygiene. Designed for interactive runs, CI, or scheduled Cloud Agent automations.
disable-model-invocation: true
---

# Maintain Agent Feature Map (`agent-map/`)

Keep `<repo-root>/agent-map/` honest as the codebase evolves. Treat the feature map as production infrastructure with a strict drift budget: inspect git churn per feature's tracked `Paths:`, update stale feature files, cover newly added surfaces, run fast verification/tests when available, and enforce contract hygiene via `validate.py`.

`$SKILL_DIR` is the directory containing this `SKILL.md`.

## Outcomes

Every run finishes with one of four outcomes:

- **`clean`** — Every `agent-map/*.md` file passed contract validation, no tracked paths drifted, and no unmapped feature surfaces appeared. No files modified.
- **`updated`** — Stale feature files, missing paths, index entries, or new feature surfaces were updated and validated cleanly.
- **`regressions-flagged`** — Map drift was updated, AND the audit uncovered suspected product regressions (behavior documented in the map that broke or vanished in code without a replacement). Product code is left untouched and the regression is highlighted.
- **`missing-map`** — No `agent-map/` exists yet. Point to `/establish-feature-map` (or run it if the user asked to set up the map).

## Hard Rules

1. **Edit only `agent-map/*.md` and `AGENTS.md` / `CLAUDE.md`.** Never modify product code or tests to make the map look right.
2. **Triage discipline (Map Drift vs. Product Regression):**
   - *Map drift:* Routes, files, flags, or sub-features intentionally evolved in code → update `agent-map/<feature>.md` and its `Paths:` header.
   - *Product regression:* A documented user path or handler broke or disappeared unintentionally → **do not silently delete it from the map**; keep the entry and report it under `Suspected Product Regressions`.
3. **Preserve `## Notes` verbatim** in every updated file.
4. **Scoped work only.** Leave `FRESH` feature files untouched unless a contract error or cross-feature link requires an edit.
5. **Follow [FEATURE-TEMPLATE.md](FEATURE-TEMPLATE.md) exactly.**

## Workflow

Copy this checklist into a todo list and track progress:

```text
- [ ] 1. Run scripts/drift.py and scripts/validate.py to measure drift & contract state
- [ ] 2. Plan triage: stale features, broken paths, unmapped churn, contract fixes
- [ ] 3. Audit & update dirty/new features (parallel subagents if >= 3 dirty features)
- [ ] 4. Reconcile agent-map/README.md and AGENTS.md
- [ ] 5. Run optional targeted verification (tests or verify-* harness if available)
- [ ] 6. Run scripts/validate.py until 0 errors
- [ ] 7. Report outcome, drift summary, and any suspected product regressions
```

### 1. Measure Drift & Contract State

Run both scripts at the start:

```bash
python3 $SKILL_DIR/scripts/drift.py <root> --summary
python3 $SKILL_DIR/scripts/validate.py <root>
```

If `drift.py` reports that `agent-map/` does not exist, stop and report `missing-map` (or invoke `establish-feature-map` if requested).

If all feature files are `FRESH`, `unmapped_recent_dirs` is empty, and `validate.py` reports 0 errors and 0 warnings, stop immediately and report **`clean`**.

### 2. Plan Triage

From the `drift.py` and `validate.py` output, categorize work:
1. **`STALE` / `BROKEN_PATHS` / `INVALID_META` feature files:** Need source diff inspection (`git diff <last_sha> HEAD -- <paths>`), content/path updates, and re-stamping `Last linted: <head_sha>`.
2. **Unmapped recent code churn (`unmapped_recent_dirs`):** Inspect those directories:
   - If they belong to an existing feature whose `Paths:` list was too narrow, add the directory to that feature's `Paths:` and update its `Code touchpoints`.
   - If they represent a brand-new user-facing feature or service flow, add a new `agent-map/<feature-slug>.md` file and index it in `agent-map/README.md`.
   - If they are pure build/infra noise, ignore them.
3. **Removed features:** If an entire feature was intentionally decommissioned in git history, remove its `agent-map/<feature>.md` (`git rm`), move any human `## Notes` into `agent-map/README.md`, and remove its row from the `README.md` index.

### 3. Audit & Update Dirty Features

- If **1–2 feature files** need updates, inspect the git diffs and update them directly.
- If **3+ feature files** need updates, dispatch parallel subagents via `Task` (`subagent_type: generalPurpose`) using [subagent-audit-prompt.md](subagent-audit-prompt.md).

 note: When a feature file's tracked paths changed *only* in internal implementation details that do not affect user behavior, verification steps, touchpoints, or gotchas, simply re-stamp `Last linted: <head_sha>` after confirming accuracy.

### 4. Reconcile `agent-map/README.md` & `AGENTS.md`

- If features were added, removed, or renamed, or if stack/harness commands changed, update `agent-map/README.md` and stamp `Last linted: <head_sha>`.
- If `validate.py` flagged `AGENTS.md` (or `CLAUDE.md`), insert or refresh the block from [agents-md-block.md](agents-md-block.md).

### 5. Targeted Verification (Static by Default + Optional Live/Test Proof)

- **Always:** Verify every cited file path, route, and script name exists in the repo.
- **When a feature's `Driving & verifying it` recipe or code touchpoints changed:**
  - If a fast, non-destructive targeted test command exists for that feature (e.g., `pytest tests/test_auth.py`, `pnpm test auth`, `go test ./internal/auth/...`) or a project verification skill (`.cursor/skills/run-verification-rig/SKILL.md` or `.cursor/skills/verify-*/SKILL.md`) is available and safe to run in the current environment, run the targeted check to confirm the recipe still works. For a full live verification pass across all features, run `/maintain-verification-rig`.
  - In headless/CI environments where live servers cannot be launched, stick to static verification and unit/integration tests and note any skipped live harness drives.

### 6. Validate

```bash
python3 $SKILL_DIR/scripts/validate.py <root>
```

Fix all errors until `validate.py` exits `0` with `0 errors, 0 warnings`.

### 7. Report

Output a concise maintenance report:
- **Outcome:** `clean` | `updated` | `regressions-flagged` | `missing-map`
- **Feature files updated / created / removed / re-stamped**
- **Verification checks run** (static + any test/harness runs)
- **Suspected Product Regressions** (if any — with file/line citations)
- **`validate.py` status**

## Resources

- [FEATURE-TEMPLATE.md](FEATURE-TEMPLATE.md) — Contract for `agent-map/README.md` and `agent-map/<feature>.md`
- [agents-md-block.md](agents-md-block.md) — Block wired into `AGENTS.md` / `CLAUDE.md`
- [subagent-audit-prompt.md](subagent-audit-prompt.md) — Prompt template for parallel feature drift auditors
- `scripts/drift.py` — Git SHA + `Paths:` staleness & unmapped churn analyzer
- `scripts/validate.py` — Contract, link, path, and staleness linter
