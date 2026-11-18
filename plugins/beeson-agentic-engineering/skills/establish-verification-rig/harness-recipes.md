# Verification Harness Recipes Across Stacks

How to interview any repository and design a reliable, repeatable verification rig in `.cursor/skills/run-verification-rig/`.

## Core Principle: Build the Lever

When agents have to invent one-off shell pipelines on every turn to launch a server, wait for readiness, run migrations, click through a UI, and clean up PIDs, they burn tokens and leak processes.

Build a small executable helper script at `.cursor/skills/run-verification-rig/scripts/rig_control.sh` (or `rig_control.py`) with composable subcommands:
- `rig_control.sh launch` — creates `$VERIFY_SCRATCH_DIR` and `$EVIDENCE_DIR`, runs migrations/seed against the scratch state, starts the target, records its PID in `$VERIFY_SCRATCH_DIR/app.pid`, and waits until `doctor` passes.
- `rig_control.sh doctor` — read-only check verifying PID liveness, port ownership, and readiness endpoint/state. Exits `0` if healthy, non-zero with a clear diagnostic otherwise.
- `rig_control.sh cleanup` — kills only PIDs recorded in `$VERIFY_SCRATCH_DIR/*.pid`, removes `$VERIFY_SCRATCH_DIR`, and verifies `$EVIDENCE_DIR` still exists on disk.

---

## Recipes by Surface Type

### 1. Web UI & Full-Stack Apps (Next.js, Vite, Remix, Rails, Django, SPA, Electron)

- **Isolation:**
  - Pick an ephemeral or dedicated verification port (e.g. `PORT=${VERIFY_PORT:-4173}`) or pass `--port` so the rig does not collide with the developer's running `localhost:3000` dev server.
  - Point SQLite / local file storage / Prisma / Drizzle at `$VERIFY_SCRATCH_DIR` (or an isolated test database/schema).
- **Readiness:**
  - Poll the HTTP health or root URL until HTTP 200 **and** verify any seed data endpoint or initial HTML payload renders (a bound port alone can still be compiling or running init scripts).
- **Driving (in priority order):**
  1. **Existing Playwright / Cypress E2E harness:** Run targeted specs or a lightweight Playwright script against the running `$VERIFY_PORT` instance, saving screenshots, ARIA snapshots, and traces into `.verification-evidence/$RUN_ID/<feature-slug>/`.
  2. **Browser / CDP / Playwright one-shot runner:** Ship a small `.cursor/skills/run-verification-rig/scripts/drive_browser.mjs` (or `.py`) that connects to the URL, executes actions by ARIA role/accessible name (`getByRole`, `getByLabel`), and dumps `snapshot.aria.txt` + `screenshot.png` to the feature's evidence folder.
- **Proof:**
  - UI action + resulting state: ARIA snapshot + screenshot with app identity visible + read-back of any persisted mutation.

### 2. CLI & TUI Applications (Go, Rust, Python, Node, C/C++)

- **Launch:**
  - Short-lived CLIs have no long-running daemon. `Launch` builds the binary once into `$VERIFY_SCRATCH_DIR/bin/<cli>` (or installs the editable package) and puts it at the front of `PATH`.
  - Every drive runs in an isolated environment (`HOME="$VERIFY_SCRATCH_DIR/home" XDG_CONFIG_HOME="$VERIFY_SCRATCH_DIR/config" TMPDIR="$VERIFY_SCRATCH_DIR/tmp"`).
- **Doctor:**
  - Verifies the binary exists at `$VERIFY_SCRATCH_DIR/bin/<cli>`, is executable, matches the current source build, and `<cli> --version` or `<cli> --help` exits `0`.
- **Driving:**
  - For standard CLIs: run `<cli> <subcommand> [flags]` (preferring `--format json` when supported) and tee `stdout`, `stderr`, and exit code into `.verification-evidence/$RUN_ID/<feature-slug>/`.
  - For interactive TUIs: drive via `tmux` (`tmux new-session -d -s "verify-$RUN_ID" ...`, `tmux send-keys`, `tmux capture-pane -p`) and save captured pane transcripts to the evidence directory.
- **Proof:**
  - Command string, `stdout`, `stderr`, exit code, and any files created/modified in `$VERIFY_SCRATCH_DIR` read back verbatim.

### 3. HTTP / GraphQL / gRPC APIs & Microservices

- **Launch & Isolation:**
  - Start the service on an isolated port with a disposable DB/store and seed fixtures.
- **Doctor:**
  - Check PID ownership of the port + `GET /health` (or readiness RPC) + verify seed fixture count.
- **Driving:**
  - Execute real HTTP/RPC calls (`curl -sS -D headers.txt -o response.json ...` or `grpcurl`) matching the caller workflows in `agent-map/<feature>.md`.
- **Proof:**
  - Request + status/headers + response body **plus** a second read-only `GET`/query proving a mutation actually persisted in storage (never trust a `200 OK` write response alone).

### 4. Background Workers, Queues & Event Pipelines

- **Launch:**
  - Start the worker process (or trigger harness) connected to an isolated queue/topic or local SQLite/Redis test db.
- **Driving:**
  - Enqueue a real job or webhook payload through the producer entry point, then poll job status until completion/failure (with a bounded timeout, never a blind `sleep`).
- **Proof:**
  - Enqueued job ID, worker log excerpt, and downstream side-effect read-back (DB row state, emitted outbox message, or written file).

### 5. Libraries, SDKs, Parsers & Compilers

- **Launch & Doctor:**
  - Build/compile the library and verify exported entrypoints exist.
- **Driving:**
  - Execute a consumer script or fixture replay against the public package boundary (importing the package the way an external user does, not calling private internal helpers).
- **Proof:**
  - Input fixture, output artifact, exit code, and diff against expected output.
