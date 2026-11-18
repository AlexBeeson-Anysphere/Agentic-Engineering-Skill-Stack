---
name: maintain-verification-rig
description: Periodic or automated upkeep pass that keeps `.cursor/skills/run-verification-rig/` and `agent-map/` honest against the live app: runs a parallel read-only source wave across `agent-map/` features, executes one coordinator-owned live regression sweep driving every feature, triages map drift vs. rig gaps vs. product regressions, re-proves any harness fixes live, and validates contract hygiene. Use for /maintain-verification-rig, auditing the verification rig, or scheduled verification automations.
disable-model-invocation: true
---

# Maintain Verification Rig (`.cursor/skills/run-verification-rig/` + `agent-map/`)

A verification rig and feature map rot the moment the application changes. This skill is the live upkeep loop for repositories using `<repo-root>/agent-map/` and `<repo-root>/.cursor/skills/run-verification-rig/`: parallel read-only source readers per feature, one coordinator-owned live session driving every feature in regression sweep order, and strict separation between **map/rig drift** and **product regressions**.

`$SKILL_DIR` is the directory that contains this `SKILL.md`. Other skills in this plugin are sibling directories of `$SKILL_DIR`.

## Outcomes

Every run finishes with one of four outcomes:

- **`clean`** — Every feature in `agent-map/` received source and live coverage; `.cursor/skills/run-verification-rig/` and `agent-map/` needed no edits.
- **`updated`** — Proven corrections to `.cursor/skills/run-verification-rig/` and/or `agent-map/*.md` were applied, re-driven live, and validated cleanly.
- **`regressions-flagged`** — Source and live coverage completed (and any map/rig drift was fixed), AND the live pass uncovered broken product behavior (`product regression`). Product code is left untouched and each regression is reported with captured proof artifacts.
- **`blocked`** — `.cursor/skills/run-verification-rig/` or `agent-map/` is missing, or coverage could not finish after fixing skill drift. Names the exact blocker.

## Edit Scope (Hard Rules)

1. **Edit only `.cursor/skills/run-verification-rig/**`, `agent-map/*.md`, and `AGENTS.md` / `CLAUDE.md`.**
2. **Never edit product code during a run.** Behavior described in `agent-map/` that the app no longer performs is either:
   - **Map / rig drift** (the product intentionally changed routes, flags, or UI labels) → update `agent-map/` or `.cursor/skills/run-verification-rig/`.
   - **Product regression** (a feature broke unintentionally) → **do not paper over it in docs and do not edit product code**; preserve the failing evidence artifact and report it.
3. **Preserve `## Notes` verbatim** in every `agent-map/*.md` file.

## Workflow

Copy this checklist into `TodoWrite` and track progress:

```text
- [ ] 1. Locate target & check baseline drift (validate_rig.py, drift.py, validate.py)
- [ ] 2. Run parallel read-only source wave across agent-map/ features
- [ ] 3. Reconcile source wave & check unmapped recent churn for missing features
- [ ] 4. Execute coordinator-owned live sweep across all features (holding the 3 invariants)
- [ ] 5. Triage findings (map drift vs. rig gap vs. product regression) & re-drive any rig fixes
- [ ] 6. Validate with validate_rig.py and validate.py until 0 errors, then report
```

### 1. Locate Target & Check Baseline Drift

Run the structural and git-drift checks first:

```bash
python3 "$SKILL_DIR/../establish-verification-rig/scripts/validate_rig.py" <root>
python3 "$SKILL_DIR/../maintain-feature-map/scripts/drift.py" <root> --summary
python3 "$SKILL_DIR/../establish-feature-map/scripts/validate.py" <root>
```

- If `agent-map/` does not exist → stop and report **`blocked`** (point to `/establish-feature-map` or `/establish-verification-rig`).
- If `.cursor/skills/run-verification-rig/SKILL.md` does not exist → stop and report **`blocked`** (point to `/establish-verification-rig`).
- Fix any broken index links in `agent-map/README.md` before starting the source wave.

### 2. Parallel Source Wave (Read-Only Subagents)

Launch read-only subagents concurrently via `Task` (`subagent_type: generalPurpose`) using [subagent-source-wave.md](subagent-source-wave.md) — one subagent per feature file (or batches of 2–3 features for large maps).

- Each subagent reads its assigned `agent-map/<feature>.md` and traces current source code to answer:
  1. How does this user-facing feature work in current code?
  2. Did any entry routes, selectors, CLI flags, startup requirements, or tracked `Paths:` drift since `Last linted: <sha>`?
  3. What is the single most concise live-verification recipe for this feature?
- **Subagents never drive the app and never edit files.**

### 3. Reconcile

1. Review every subagent's returned summary and spot-check cited drift.
2. Inspect `unmapped_recent_dirs` from `drift.py`: if recent commits added a new user-facing surface with a concrete source path, add a new `agent-map/<feature-slug>.md` file (following `$SKILL_DIR/../establish-feature-map/FEATURE-TEMPLATE.md`) and index it in `agent-map/README.md`.
3. Generate the ordered live sweep plan:
   ```bash
   python3 .cursor/skills/run-verification-rig/scripts/rig_map.py <root> --mode sweep
   ```
   Merge overlapping preconditions so the live pass transitions through as few app restarts as practical.

### 4. Coordinator-Owned Live Pass (Mandatory)

**Required even when the source wave reports zero drift.** The coordinator owns all app driving, following `.cursor/skills/run-verification-rig/SKILL.md` (`Launch`, `Doctor`, `Drive`, `Evidence`, `Cleanup`):

- Follow the rig's launch model: one long-lived instance driven serially in sweep order for servers/UIs, or a fresh isolated session per drive for short-lived CLIs.
- Exercise **every** mapped feature in `agent-map/README.md` at least once, holding **three strict invariants** across the entire run:
  1. **Never drive an un-doctored instance:** Run **Doctor** before the first drive, on each fresh session (when sessions are the unit), and immediately after any failed or surprising drive. Where Doctor cannot see the failure (e.g., a wedged modal/UI state on a healthy server process), reset to baseline state or relaunch rather than hoping.
  2. **Evidence captured so far survives every cleanup:** Check on disk that `.verification-evidence/<run-id>/` still holds all captured artifacts after every reset or cleanup.
  3. **Nothing a drive started outlives that drive's usefulness:** Clean failed-iteration residue whether the session is stuck, exited, or shared.
- **Handling Doctor failures from rig drift:** If **Doctor** or **Launch** fails because a port, env var, or startup script changed in the repo, fix `.cursor/skills/run-verification-rig/` under edit scope and retry once (restarting only what the fix invalidated) before calling the run **`blocked`**.
- **Unreachable features (`verified-unreachable`):** A feature may be marked `verified-unreachable` **only** by recording the concrete external prerequisite (entitlement, external credential, OS hardware) and the exact command attempted. If `agent-map/<feature>.md` omitted that prerequisite, add it to `Preconditions:` / `Gotchas` as map drift.

### 5. Triage & Re-Proof

Classify every discrepancy discovered during the source wave and live pass:

1. **Map drift** (wrong or outdated user-POV entry point, selector, CLI flag, touchpoint, or missing precondition in `agent-map/<feature>.md`):
   - Update `agent-map/<feature>.md` (preserving `## Notes` verbatim) and stamp `Last linted: <head_sha>`.
2. **Rig / harness gap** (working product behavior that `.cursor/skills/run-verification-rig/` could not drive or observe cleanly):
   - Update `.cursor/skills/run-verification-rig/SKILL.md` and/or its executable scripts under `.cursor/skills/run-verification-rig/scripts/` (`chmod +x`), stamp `Last verified: <head_sha>`, and **re-drive the affected feature(s) live** to prove the harness fix works before teardown!
3. **Product regression** (product behavior documented in `agent-map/` that failed or vanished unintentionally at runtime):
   - Leave product code untouched.
   - Leave the expected behavior in `agent-map/<feature>.md`.
   - Retain the failing proof artifact (screenshot, ARIA snapshot, HTTP response, or CLI output) in `.verification-evidence/<run-id>/<feature-slug>/` and list it under **Product Regressions**.

Run final **Cleanup** after the last drive (including any re-proofs) so zero processes or scratch dirs outlive the run, while `.verification-evidence/<run-id>/` remains on disk.

### 6. Validate & Report

Run both validators until they exit `0` with `0 errors`:

```bash
python3 "$SKILL_DIR/../establish-verification-rig/scripts/validate_rig.py" <root> --require-evidence .verification-evidence/<run-id>
python3 "$SKILL_DIR/../establish-feature-map/scripts/validate.py" <root>
```

Output a concise report:
- **Outcome:** `clean` | `updated` | `regressions-flagged` | `blocked`
- **Coverage:** Features sourced and driven live (with evidence paths under `.verification-evidence/<run-id>/`), plus any `verified-unreachable` features and their prerequisites
- **Map / Rig Drift Fixed:** Files updated in `agent-map/` or `.cursor/skills/run-verification-rig/`
- **Product Regressions:** Broken product behaviors caught live, with exact repro commands and artifact pointers (or `none`)
- **Validation status:** `validate_rig.py` and `validate.py` results

## Resources

- [subagent-source-wave.md](subagent-source-wave.md) — Read-only source auditor prompt template for Step 2
- `$SKILL_DIR/../establish-verification-rig/RIG-SKILL-TEMPLATE.md` — Contract for `.cursor/skills/run-verification-rig/SKILL.md`
- `$SKILL_DIR/../establish-feature-map/FEATURE-TEMPLATE.md` — Contract for `agent-map/README.md` and `agent-map/<feature>.md`
