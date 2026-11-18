---
name: establish-verification-rig
description: Interviews a repository to build a project-local verification rig at `.cursor/skills/run-verification-rig/` integrated with the repository's `agent-map/` feature map, upgrades `agent-map/` verification recipes, and proves the rig end-to-end on a live feature before hand-off. Works on any stack (web UI, CLI/TUI, API, worker, desktop, library). Use when setting up a verification harness, creating `run-verification-rig`, or giving agents a scripted way to drive and prove app behavior.
disable-model-invocation: true
---

# Establish Verification Rig (`.cursor/skills/run-verification-rig/`)

Build a project-local verification skill at `<repo-root>/.cursor/skills/run-verification-rig/` that teaches any agent how to launch, health-check (`Doctor`), drive, capture evidence for, and clean up the real application—integrated directly with `<repo-root>/agent-map/`.

Inspired by Lauren Tan's `pstack` verification rig (`create-verification-skill` + `principle-prove-it-works` + `principle-build-the-lever`), adapted so the landscape lives in `<repo-root>/agent-map/` and the execution rig lives in `<repo-root>/.cursor/skills/run-verification-rig/`.

`$SKILL_DIR` is the directory that contains this `SKILL.md`. Other skills in this plugin are sibling directories of `$SKILL_DIR`.

## What a Finished Run Produces

1. **`<repo-root>/agent-map/` (verified present & valid)** — If `agent-map/` does not exist yet, this skill runs `/establish-feature-map` (`$SKILL_DIR/../establish-feature-map/SKILL.md`) first so there is a single unified feature map.
2. **`.cursor/skills/run-verification-rig/SKILL.md`** — Project-local verification skill following [RIG-SKILL-TEMPLATE.md](RIG-SKILL-TEMPLATE.md) with zero placeholders:
   - `## Execution Modes (Integrated with agent-map/)` (`diff`, `feature <slug>`, and `sweep`)
   - `## Launch` (isolated scratch state, migrations/seed, readiness check)
   - `## Doctor` (read-only liveness, port ownership, and baseline state check)
   - `## Drive` (real selectors, CLI commands, or API calls)
   - `## Evidence` (proof standards by change type, stored in `.verification-evidence/<run-id>/`)
   - `## Cleanup` (PID-scoped teardown that preserves `.verification-evidence/<run-id>/`)
   - `## Helpers` (documented executable scripts)
3. **`.cursor/skills/run-verification-rig/scripts/`** — Executable (`chmod +x`) helpers:
   - `rig_map.py` (copied from `$SKILL_DIR/scripts/rig_map.py`) to map git diffs, individual features, or full regression sweeps from `agent-map/`.
   - Optional `rig_control.sh` (or `rig_control.py`) wrapping `launch`, `doctor`, and `cleanup` per [harness-recipes.md](harness-recipes.md).
4. **Updated `agent-map/` & `AGENTS.md`** — `agent-map/README.md` (`## Baseline & verification harness`) wired to `.cursor/skills/run-verification-rig/SKILL.md`, and `agent-map/<feature>.md` (`## Driving & verifying it`) grounded in real rig commands.
5. **Live end-to-end proof** — The generated skill has been executed once end-to-end (`Launch → Doctor → Drive 1 feature from agent-map/ → Capture Evidence → Cleanup → Confirm evidence survived cleanup`) and passed `validate_rig.py`.

## Hard Rules

1. **Interview the repo, not the user.** Answer surface, run command, drive harness, evidence shape, and isolation from manifests, code, and configs first. Ask the user only what cannot be observed in the repo.
2. **Never invent a second feature map.** Do not create `.cursor/skills/verify-*/features/`. All feature journeys live in `<repo-root>/agent-map/<feature>.md`.
3. **Fix or report startup blockers before generating.** If the checkout does not build or start as-is, fix verification scaffolding issues (or report broken product startup precisely) rather than writing a rig against broken steps. Any temporary scaffolding created for startup must be removed in `Cleanup`.
4. **Never kill by generic process name.** `Cleanup` must only stop PIDs/containers started by the verification run, and must **never** delete `.verification-evidence/`.
5. **A generated skill that was never executed is a draft, not a deliverable.** You must prove the rig live on at least one feature in `agent-map/` before finishing.

## Workflow

Copy this checklist into `TodoWrite` and track progress:

```text
- [ ] 1. Run scripts/inspect_rig.py to inventory surfaces, scripts, harnesses, and agent-map/ state
- [ ] 2. Ensure agent-map/ exists (run establish-feature-map if missing)
- [ ] 3. Interview the codebase (Surface, Launch, Doctor, Drive, Evidence, Isolate/Cleanup)
- [ ] 4. Generate .cursor/skills/run-verification-rig/SKILL.md and executable scripts/ helpers
- [ ] 5. Wire agent-map/README.md, agent-map/<feature>.md recipes, and AGENTS.md
- [ ] 6. Prove the rig live end-to-end on 1 mapped feature (Launch -> Doctor -> Drive -> Evidence -> Cleanup)
- [ ] 7. Validate with validate_rig.py and establish-feature-map/scripts/validate.py, then report
```

### 1. Run Repo Inspection

```bash
python3 "$SKILL_DIR/scripts/inspect_rig.py" <root> --summary
```

### 2. Ensure `agent-map/` Exists

Check the `agent-map/` status in the `inspect_rig.py` output:
- If `agent-map/` is **missing**, read `$SKILL_DIR/../establish-feature-map/SKILL.md` and execute it first to build `<root>/agent-map/README.md` and `<root>/agent-map/<feature>.md`.
- If `agent-map/` **exists**, run `python3 "$SKILL_DIR/../establish-feature-map/scripts/validate.py" <root>` to check its current state.

### 3. Interview the Codebase

Read the manifests, entrypoints, existing test/E2E configs, and [harness-recipes.md](harness-recipes.md) to establish:
- **Surface:** What does a user or caller touch? (Web UI, CLI/TUI, REST/GraphQL/gRPC API, Desktop app, Worker, SDK/Library). If multiple exist, identify the primary surface and note the secondary ones.
- **Launch:** How to start the app from an empty scratch directory (`VERIFY_SCRATCH_DIR=/tmp/<slug>-verify-$RUN_ID`), run migrations/seed data, and verify it is **ready and usable** (not merely that a port is open while initialization is still running). For short-lived CLIs, `Launch` means build once and run each drive in an isolated environment.
- **Doctor:** A single read-only check that verifies process liveness, port ownership by our PID, expected build/revision, and clean baseline state.
- **Drive (Build the Lever):** Prefer existing repo harnesses (Playwright, Cypress, CLI binary, HTTP endpoints) wrapped in clean commands. Use stable handles (ARIA roles/names, `data-testid`, route paths, CLI flags with `--format json`).
- **Evidence:** What artifacts prove behavior for this app's surfaces, stored under `.verification-evidence/$RUN_ID/<feature-slug>/`. Ensure `.verification-evidence/` is ignored in `.gitignore` (or note it as a local working artifact).
- **Isolate & Cleanup:** Whether two runs can execute concurrently (via dynamic port + `$VERIFY_SCRATCH_DIR`) or must check a lock in `Doctor`. Cleanup stops only recorded PIDs/containers and removes `$VERIFY_SCRATCH_DIR` while leaving `.verification-evidence/$RUN_ID/` intact.

### 4. Generate `.cursor/skills/run-verification-rig/`

1. Create `<root>/.cursor/skills/run-verification-rig/scripts/`.
2. Copy `$SKILL_DIR/scripts/rig_map.py` into `<root>/.cursor/skills/run-verification-rig/scripts/rig_map.py` and `chmod +x` it.
3. Where a control script simplifies lifecycle management (`launch`, `doctor`, `cleanup`), write `<root>/.cursor/skills/run-verification-rig/scripts/rig_control.sh` (or `.py`), `chmod +x` it, and document its exact subcommands in `SKILL.md`.
4. Write `<root>/.cursor/skills/run-verification-rig/SKILL.md` following [RIG-SKILL-TEMPLATE.md](RIG-SKILL-TEMPLATE.md) with real commands, selectors, ports, and paths from the repo (zero placeholders).

### 5. Wire `agent-map/` and `AGENTS.md`

1. In `agent-map/README.md`, update `## Baseline & verification harness` so `Verification skill / harness:` points to [`.cursor/skills/run-verification-rig/SKILL.md`](../.cursor/skills/run-verification-rig/SKILL.md) and lists the exact `Launch`, `Doctor`, and `rig_map.py` commands.
2. In each `agent-map/<feature>.md`, review `## Driving & verifying it` and `## Gotchas (what usually lies)`:
   - Ensure every feature's driving steps use the real rig commands and specify an `Observable result:`.
   - If seed data lacks a precondition a journey needs, record that in `Preconditions:` and `Gotchas` rather than weakening the journey.
   - Re-stamp `Last linted: <short-sha>` on any updated `agent-map/*.md` file.
3. Ensure root `AGENTS.md` (and `CLAUDE.md` if present) carries the updated `<!-- agent-map:start -->` block from `$SKILL_DIR/../establish-feature-map/agents-md-block.md` mentioning `.cursor/skills/run-verification-rig/SKILL.md`.

### 6. Prove the Generated Rig Live (Mandatory)

Execute the newly generated `.cursor/skills/run-verification-rig/SKILL.md` end-to-end on **at least one** feature from `agent-map/`:
1. Run `python3 .cursor/skills/run-verification-rig/scripts/rig_map.py . --mode feature <slug> --run-id proof-run` to print the feature plan.
2. Execute **Launch** from a clean `$VERIFY_SCRATCH_DIR`.
3. Execute **Doctor** and confirm it exits `0`.
4. Execute **Drive** for `<slug>` following its `agent-map/<slug>.md` recipe and save real proof artifacts to `.verification-evidence/proof-run/<slug>/`.
5. Execute **Cleanup** to tear down the launched instance and `$VERIFY_SCRATCH_DIR`. (If any iteration fails while debugging the rig, run **Cleanup** before retrying so no ports or processes are stranded.)
6. Confirm proof survived cleanup by running `validate_rig.py --require-evidence .verification-evidence/proof-run/<slug>`.

If proving in a stand-in environment (e.g., a headless container without an external third-party credential), explicitly list every setup step or external dependency that remains unverified on the real target.

### 7. Validate & Report

Run both validators until they exit `0` with `0 errors`:

```bash
python3 "$SKILL_DIR/scripts/validate_rig.py" <root> --require-evidence .verification-evidence/proof-run
python3 "$SKILL_DIR/../establish-feature-map/scripts/validate.py" <root>
```

Report to the user:
- Surfaces & harness levers wired in `.cursor/skills/run-verification-rig/`
- Execution modes available (`diff`, `feature <slug>`, `sweep`)
- Live proof summary (feature driven, commands executed, evidence artifacts saved at `.verification-evidence/proof-run/`)
- Validator results (`validate_rig.py` + `validate.py`)
- Point to `/maintain-verification-rig` for periodic/automated live regression sweeps and drift upkeep.

## Resources

- [RIG-SKILL-TEMPLATE.md](RIG-SKILL-TEMPLATE.md) — Exact contract for `.cursor/skills/run-verification-rig/SKILL.md`
- [harness-recipes.md](harness-recipes.md) — Stack-by-stack recipes for Launch, Doctor, Drive, Evidence, and Cleanup
- `scripts/inspect_rig.py` — Repo surface, script, port, and harness inspector
- `scripts/rig_map.py` — `agent-map/` plan resolver shipped into `.cursor/skills/run-verification-rig/scripts/rig_map.py`
- `scripts/validate_rig.py` — Linter for `.cursor/skills/run-verification-rig/`, `agent-map/` wiring, and surviving proof artifacts
