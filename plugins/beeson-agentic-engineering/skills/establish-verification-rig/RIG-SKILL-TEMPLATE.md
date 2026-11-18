# Template for `.cursor/skills/run-verification-rig/SKILL.md`

Every generated project verification skill lives at `<repo-root>/.cursor/skills/run-verification-rig/SKILL.md` with its executable helpers in `<repo-root>/.cursor/skills/run-verification-rig/scripts/`.

Follow this contract exactly. `validate_rig.py` checks the YAML frontmatter, metadata comment, section headings, section order, absence of placeholders, and executable permissions on `scripts/*`.

---

````markdown
---
name: run-verification-rig
description: Launch, doctor, drive, and verify <App / Repo Name> across its real surfaces (<Web UI / CLI / API / Worker / etc.>) using the `agent-map/` feature map, and capture proof artifacts that survive cleanup. Use for /run-verification-rig, proving code changes before committing or opening a PR, reproducing bugs on the real surface, or running a full regression sweep.
disable-model-invocation: true
---

# Run Verification Rig — <App / Repo Name>

<!-- verification-rig v1 | Last verified: <short-git-sha> | Surface: <primary-surface> | Map: agent-map/README.md -->

Project-local verification harness for `<App / Repo Name>`. It drives the real application the way a user or caller does, using [`agent-map/README.md`](../../../agent-map/README.md) and [`agent-map/<feature>.md`](../../../agent-map/) as the source of truth for feature journeys, preconditions, and gotchas.

A passing build, typecheck, or mocked unit test is **not** verification proof. Every verification run must launch/check the real target, drive the mapped user/caller journey, capture durable artifacts under `.verification-evidence/<run-id>/`, tear down scratch state, and confirm the proof survived cleanup.

## Execution Modes (Integrated with agent-map/)

Always resolve your verification plan first with `scripts/rig_map.py`:

### 1. `diff` Mode (Default after code changes)
Maps modified files in git against every `agent-map/<feature>.md`'s tracked `Paths:`, automatically includes prerequisite features (`Depends on features:`), and orders them according to `agent-map/README.md`'s regression sweep order.

```bash
python3 .cursor/skills/run-verification-rig/scripts/rig_map.py . --mode diff
# Or against a base branch/commit:
python3 .cursor/skills/run-verification-rig/scripts/rig_map.py . --mode diff --base origin/main
```

### 2. `feature` Mode (Targeted feature verification or bug reproduction)
Loads one or more specific `agent-map/<slug>.md` features (plus any prerequisite features they depend on) in sweep order.

```bash
python3 .cursor/skills/run-verification-rig/scripts/rig_map.py . --mode feature <feature-slug>
```

### 3. `sweep` Mode (Full top-to-bottom regression sweep)
Loads every feature in `agent-map/README.md`'s `## Features (regression sweep order)` from top to bottom.

```bash
python3 .cursor/skills/run-verification-rig/scripts/rig_map.py . --mode sweep
```

**Three invariants for every run (especially `sweep`):**
1. **Never drive an un-doctored instance:** Run **Doctor** before the first drive, on each fresh session (when sessions are the unit), and immediately after any failed or surprising step. If Doctor passes on a process whose UI/state is wedged, reset state or relaunch before continuing.
2. **Evidence survives every cleanup:** Confirm proof artifacts exist on disk at `.verification-evidence/<run-id>/` after every cleanup or reset.
3. **Nothing started outlives its drive:** Clean failed-iteration residue whether the session is stuck, exited, or shared. Run **Cleanup** after the final drive of the run.

## Launch

<Ground every bullet below in this repository's real commands, ports, env vars, and data stores. Leave zero placeholders.>

- **Isolation & scratch state:**
  - Set `RUN_ID=${RUN_ID:-$(date -u +"run-%Y%m%d-%H%M%S")}`
  - Set `VERIFY_SCRATCH_DIR="/tmp/<repo-slug>-verify-$RUN_ID"` and `EVIDENCE_DIR=".verification-evidence/$RUN_ID"`
  - Create both directories: `mkdir -p "$VERIFY_SCRATCH_DIR" "$EVIDENCE_DIR"`
  - **Concurrency policy:** <State clearly whether two verification runs can run side-by-side via isolated ports/data dirs, OR if they share a fixed port/resource and must refuse to double-drive when another instance is running.>
- **Database / state bootstrap (from an empty scratch state):**
  - `<exact migration + seed command, e.g., DATABASE_URL="file:$VERIFY_SCRATCH_DIR/test.db" pnpm db:push && pnpm db:seed>`
- **Start command:**
  - `<exact command to start the server/UI/worker in background recording PID to $VERIFY_SCRATCH_DIR/app.pid, OR exact one-time build command for a short-lived CLI/TUI>`
- **Readiness check (usable, not just process alive):**
  - `<exact command/check proving migrations/seed finished and the surface is ready to serve requests or render UI>`

## Doctor

Run this read-only check before the first drive and after any unexpected behavior:

```bash
<exact doctor command or script invocation, e.g., .cursor/skills/run-verification-rig/scripts/rig_control.sh doctor>
```

Doctor verifies:
- **Process & ownership:** The PID in `$VERIFY_SCRATCH_DIR/app.pid` is alive and owns the expected port (`<port>`), or the CLI binary matches the current checkout build.
- **State & revision:** Connected to the disposable `$VERIFY_SCRATCH_DIR` data store (never production or the developer's personal dev DB) with baseline seed state intact.
- **Health & auth:** `<health endpoint / initial screen / auth token check>` responds cleanly.

## Drive

Open the target `agent-map/<feature>.md` file(s) output by `rig_map.py` and execute each step in `## Driving & verifying it` while respecting `## Gotchas (what usually lies)`:

- **Primary surface (`<Web UI / CLI / API / etc.>`):**
  - <Exact harness commands for this repo: e.g., Playwright/CDP commands, CLI invocations with `--format json`, or `curl`/HTTP requests against the launched instance.>
  - **Stable handles:** Prefer `<ARIA roles and accessible names / data-testid / CLI flags / route paths>` over CSS selectors, coordinates, or fixed `sleep` calls.
- **Secondary surfaces (if any):**
  - <Exact commands to drive secondary surfaces or inspect background worker queues/DB state.>
- **Handling unmet preconditions:**
  - If seed data or the environment lacks a precondition listed in `agent-map/<feature>.md`, report `verified-unreachable` with the exact attempted command and unmet prerequisite—**never weaken the journey to make it pass**.

## Evidence

Write all proof artifacts for a feature into `.verification-evidence/$RUN_ID/<feature-slug>/`:

- **Proof standards by change type:**
  - **UI flows:** Capture both the user action and resulting state—save an ARIA/DOM snapshot (`*.aria.txt` or `*.html`) and screenshot (`*.png`) showing the app identity and observable result.
  - **CLI commands:** Save the exact command, stdout (`*.stdout.txt`), stderr (`*.stderr.txt`), and exit code (`*.exitcode`).
  - **API / state mutations:** Save the mutation response (`*.response.json`) **plus** a read-only second view or DB read-back (`*.readback.json`) confirming persistence.
  - **Migrations / parsers:** Save the replayed input and before/after output diff (`*.diff.txt`).
  - **Performance changes:** Save before/after traces or benchmark runs (`*.bench.txt`).
- **Dry-run / test-mode caution:** When using a dry-run or sandbox flag, verify by observation (files, network logs, git refs) what it actually skipped rather than trusting the flag name.

## Cleanup

Always run cleanup after finishing the verification pass—and after any failed iteration—so broken attempts never strand processes or ports:

```bash
<exact cleanup command or script invocation, e.g., .cursor/skills/run-verification-rig/scripts/rig_control.sh cleanup>
```

Cleanup rules:
1. **Kill only what this run started:** Stop PIDs recorded in `$VERIFY_SCRATCH_DIR/*.pid` (or containers tagged with `$RUN_ID`). **Never** run `killall` or `pkill` by generic process name (`node`, `python`, `postgres`, `go`).
2. **Remove scratch state only:** Delete `$VERIFY_SCRATCH_DIR`.
3. **Preserve evidence:** Never delete `.verification-evidence/$RUN_ID/`. Immediately after cleanup, run:
   ```bash
   ls -la ".verification-evidence/$RUN_ID/"
   ```
   and confirm the captured proof files exist and are non-empty. (Also ensure `.verification-evidence/` is in `.gitignore` unless the user asked to commit the proof trail.)

## Helpers

Every helper script shipped in `.cursor/skills/run-verification-rig/scripts/` is executable (`chmod +x`):

- **`.cursor/skills/run-verification-rig/scripts/rig_map.py`** — Parses `agent-map/README.md` and `agent-map/<feature>.md` to produce ordered verification plans for `--mode diff`, `--mode feature <slug>`, and `--mode sweep`.
- **`<optional: .cursor/skills/run-verification-rig/scripts/rig_control.sh or control-<app>>`** — `<Exact usage: launch | doctor | drive | cleanup>`
````
